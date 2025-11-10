"""
RQ worker for document ingestion.
Handles PDF processing, chunking, embedding, and summary generation.
"""
import os
from datetime import datetime
import asyncio
from typing import List, Dict, Any
from pathlib import Path
from loguru import logger
from ..config import config
from ..db import couch_client
from ..vector import vector_client
from ..utils.pdf import PDFProcessor
from ..utils.chunking import chunk_page_text
from ..utils.embeddings import get_embedding_client
from ..utils.llm import get_chat_client


async def ingest_document(
    doc_id: str,
    embedding_provider: str = "openai_small",
    summary_llm_provider: str = "gpt",
    summary_llm_model: str = "gpt-4o-mini"
):
    """
    Ingest a PDF document: extract text, generate previews, create embeddings.
    
    Args:
        doc_id: Document ID in CouchDB
        embedding_provider: Embedding provider to use
        summary_llm_provider: LLM provider for summaries
        summary_llm_model: LLM model for summaries
    """
    logger.info(f"Starting ingestion for document: {doc_id}")
    
    try:
        # Get document from CouchDB
        doc = couch_client.get_doc(config.documents_db, doc_id)
        if not doc:
            raise ValueError(f"Document {doc_id} not found")
        
        file_path = doc["file_path"]
        if not os.path.exists(file_path):
            raise ValueError(f"PDF file not found: {file_path}")
        
        # Open once to get page_count, then process pages concurrently
        with PDFProcessor(file_path) as pdf_processor:
            page_count = pdf_processor.page_count

        # Update document with page count
        couch_client.update_doc(config.documents_db, doc_id, {"page_count": page_count})

        # Create preview directory for this document
        preview_dir = Path(config.preview_dir) / doc_id
        preview_dir.mkdir(parents=True, exist_ok=True)

        # Get embedding client and vector collection
        embedding_client = get_embedding_client(embedding_provider)
        collection_name = vector_client.get_collection_for_provider(embedding_provider)

        # Ensure collection exists
        vector_size = vector_client.get_vector_size_for_provider(embedding_provider)
        vector_client.create_collection_if_not_exists(collection_name, vector_size)

        # Get LLM client for summaries/vision
        llm_client = get_chat_client(summary_llm_provider, summary_llm_model)

        # Directory for extracted images
        images_dir = preview_dir / "images"

        # Concurrency control
        semaphore = asyncio.Semaphore(max(1, config.ingestion_concurrency))

        async def process_page(page_no: int):
            async with semaphore:
                logger.info(f"Processing page {page_no + 1}/{page_count} of document {doc_id}")
                preview_path = str(preview_dir / f"page_{page_no}.png")
                try:
                    # Open PDF per task to avoid thread-safety issues
                    def _extract_all():
                        with PDFProcessor(file_path) as local_pdf:
                            return local_pdf.extract_all_page_content(page_no, images_output_dir=str(images_dir))
                    content = await asyncio.to_thread(_extract_all)

                    # Generate preview image
                    def _gen_preview():
                        with PDFProcessor(file_path) as local_pdf:
                            local_pdf.generate_page_preview(page_no, preview_path)
                    await asyncio.to_thread(_gen_preview)

                    # Combine and rewrite via vision LLM
                    combined_content = _combine_page_content(content)
                    logger.info(f"Using {summary_llm_provider} ({summary_llm_model}) vision to extract and rewrite content from page {page_no}")
                    rewritten_text = await _extract_and_rewrite_content(
                        llm_client,
                        summary_llm_provider,
                        summary_llm_model,
                        preview_path,
                        combined_content,
                        page_no
                    )
                    text = rewritten_text if rewritten_text.strip() else combined_content

                    # Log content diagnostics
                    logger.info(f"Page {page_no + 1} content (first 500 chars): {text[:500]}")
                    logger.info(f"Page {page_no + 1} total text length: {len(text)} chars")
                    logger.info(f"Page {page_no + 1} extracted: {len(content['tables'])} tables, {len(content['images'])} images")

                    # Chunk and embed
                    chunks = chunk_page_text(text, page_no) if text.strip() else []
                    if chunks:
                        chunk_texts = [chunk["text"] for chunk in chunks]
                        embeddings = await embedding_client.embed(chunk_texts)

                        # Prepare chunk metadata
                        chunk_data = []
                        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                            chunk_data.append({
                                "doc_id": doc_id,
                                "page_no": page_no,
                                "chunk_index": idx,
                                "text": chunk["text"],
                                "metadata": {"token_count": chunk.get("token_count", 0)}
                            })

                        # Upsert to vector DB (blocking)
                        await asyncio.to_thread(vector_client.upsert_chunks, collection_name, chunk_data, embeddings)
                        logger.debug(f"Upserted {len(chunks)} chunks for page {page_no}")

                    # Summary and key terms
                    summary = ""
                    key_terms = []
                    if text.strip():
                        summary, key_terms = await _generate_summary_and_terms(text, llm_client, page_no)

                    # Save page doc (blocking)
                    page_doc = {
                        "_id": f"{doc_id}_page_{page_no}",
                        "type": "page",
                        "document_id": doc_id,
                        "page_no": page_no,
                        "text": text,
                        "summary": summary,
                        "key_terms": key_terms,
                        "preview_image_path": preview_path,
                        "ready": True,
                        "created_at": datetime.utcnow().isoformat()
                    }
                    await asyncio.to_thread(couch_client.save_doc, config.pages_db, page_doc)
                    logger.info(f"Page {page_no} marked as ready")

                except Exception as e:
                    logger.error(f"Error processing page {page_no}: {e}")
                    error_doc = {
                        "_id": f"{doc_id}_page_{page_no}",
                        "type": "page",
                        "document_id": doc_id,
                        "page_no": page_no,
                        "text": "",
                        "summary": "",
                        "key_terms": [],
                        "preview_image_path": "",
                        "ready": False,
                        "error": str(e),
                        "created_at": datetime.utcnow().isoformat()
                    }
                    await asyncio.to_thread(couch_client.save_doc, config.pages_db, error_doc)

        # Launch pages with bounded concurrency
        tasks = [asyncio.create_task(process_page(p)) for p in range(page_count)]
        await asyncio.gather(*tasks)
        
        # Update document status
        couch_client.update_doc(config.documents_db, doc_id, {
            "ingestion_completed": True,
            "ingestion_completed_at": datetime.utcnow().isoformat(),
            "embedding_provider": embedding_provider
        })
        
        logger.info(f"Successfully ingested document {doc_id}")
        
    except Exception as e:
        logger.error(f"Error ingesting document {doc_id}: {e}")
        # Update document with error status
        couch_client.update_doc(config.documents_db, doc_id, {
            "ingestion_failed": True,
            "ingestion_error": str(e),
            "ingestion_failed_at": datetime.utcnow().isoformat()
        })
        raise


def _combine_page_content(content: Dict[str, Any]) -> str:
    """
    Combine extracted text, tables, and images into a comprehensive text representation.
    
    Args:
        content: Dict with 'text', 'tables', and 'images'
    
    Returns:
        Combined text representation
    """
    parts = []
    
    # Add main text
    if content.get("text"):
        parts.append("TEXT CONTENT:")
        parts.append(content["text"])
        parts.append("")
    
    # Add tables
    if content.get("tables"):
        parts.append("TABLES:")
        for idx, table in enumerate(content["tables"]):
            parts.append(f"Table {idx + 1}:")
            parts.append(table.get("text", ""))
            parts.append("")
    
    # Note about images (actual image content will be extracted via vision)
    if content.get("images"):
        parts.append(f"IMAGES: {len(content['images'])} image(s) found on this page")
        parts.append("(Image content will be extracted and described)")
    
    return "\n".join(parts)


async def _extract_and_rewrite_content(
    llm_client,
    provider: str,
    model: str,
    image_path: str, 
    extracted_content: str,
    page_no: int
) -> str:
    """
    Extract all content from page image using LLM vision and rewrite it in simple, clear English.
    
    Args:
        llm_client: LLM client with vision support
        provider: LLM provider name ('gpt', 'claude', 'gemini')
        model: Model name
        image_path: Path to the page image
        extracted_content: Previously extracted text/tables content
        page_no: Page number
    
    Returns:
        Rewritten content in simple English
    """
    import base64
    from pathlib import Path
    
    try:
        # Read image and encode to base64
        image_file = Path(image_path)
        if not image_file.exists():
            logger.error(f"Image file not found: {image_path}")
            return extracted_content
        
        with open(image_path, "rb") as f:
            image_bytes = f.read()
            image_data = base64.b64encode(image_bytes).decode('utf-8')
        
        # Create prompt for rewriting content
        prompt = """Extract ALL content from this PDF page image - including text, tables, images, diagrams, charts, and any other visual elements.

Then rewrite the entire content in simple, clear English. Do NOT summarize - rewrite everything fully but in simpler language. 

Requirements:
- Preserve all information and details
- Make the language simpler and easier to understand
- Keep all data from tables, but present it clearly
- Describe images, diagrams, and charts in detail
- Maintain the structure and organization
- Use clear, straightforward language

Return the complete rewritten content."""
        
        provider_lower = provider.lower()
        
        # Handle OpenAI GPT (supports vision)
        if provider_lower == "gpt":
            if hasattr(llm_client, 'client'):
                from openai import AsyncOpenAI
                if isinstance(llm_client.client, AsyncOpenAI):
                    # Use vision-capable model (gpt-4o or gpt-4-turbo)
                    vision_model = "gpt-4o" if "gpt-4o" in model.lower() or "mini" in model.lower() else "gpt-4-turbo"
                    
                    response = await llm_client.client.chat.completions.create(
                        model=vision_model,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": prompt
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/png;base64,{image_data}"
                                        }
                                    }
                                ]
                            }
                        ],
                        max_tokens=8000
                    )
                    rewritten_text = response.choices[0].message.content
                    logger.info(f"Rewritten {len(rewritten_text)} characters from page {page_no} using {provider} ({vision_model}) vision")
                    return rewritten_text.strip()
        
        # Handle Anthropic Claude (supports vision)
        elif provider_lower == "claude":
            if hasattr(llm_client, 'client') and hasattr(llm_client, 'model'):
                claude_model = llm_client.model
                claude_client = llm_client.client
                
                # Try to use messages.create() - this should work based on ClaudeClient implementation
                try:
                    # Log client info for debugging
                    logger.debug(f"Claude client type: {type(claude_client)}")
                    logger.debug(f"Claude client attributes: {[attr for attr in dir(claude_client) if not attr.startswith('_')]}")
                    
                    # Check if messages attribute exists
                    if not hasattr(claude_client, 'messages'):
                        logger.error(f"Claude client missing 'messages' attribute. Client type: {type(claude_client)}")
                        # Try alternative: maybe it's a resource accessor pattern
                        # In some SDK versions, resources might be accessed differently
                        raise AttributeError(f"Claude client missing 'messages' attribute. Available: {[a for a in dir(claude_client) if not a.startswith('_')]}")
                    
                    response = await claude_client.messages.create(
                        model=claude_model,
                        max_tokens=8000,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": "image/png",
                                            "data": image_data
                                        }
                                    },
                                    {
                                        "type": "text",
                                        "text": prompt
                                    }
                                ]
                            }
                        ]
                    )
                    rewritten_text = response.content[0].text
                    logger.info(f"Rewritten {len(rewritten_text)} characters from page {page_no} using {provider} ({claude_model}) vision")
                    return rewritten_text.strip()
                except Exception as e:
                    logger.error(f"Claude API error: {e}. Client type: {type(claude_client)}")
                    # Re-raise to be caught by outer exception handler
                    raise
        
        # Handle Google Gemini (supports vision natively)
        elif provider_lower == "gemini":
            if hasattr(llm_client, 'model'):
                from PIL import Image as PILImage
                import io
                
                # Load image for Gemini
                image_pil = PILImage.open(io.BytesIO(image_bytes))
                
                # Use the model's generate_content with image
                response = await llm_client.model.generate_content_async(
                    [prompt, image_pil],
                    generation_config={
                        "max_output_tokens": 8000,
                        "temperature": 0.3
                    }
                )
                rewritten_text = response.text
                logger.info(f"Rewritten {len(rewritten_text)} characters from page {page_no} using {provider} ({model}) vision")
                return rewritten_text.strip()
        
        logger.warning(f"LLM provider {provider} does not support vision API or client not properly configured, using extracted content as-is")
        return extracted_content
        
    except Exception as e:
        logger.error(f"Error extracting and rewriting content from image for page {page_no} using {provider}: {e}")
        return extracted_content


async def _generate_summary_and_terms(
    text: str,
    llm_client,
    page_no: int
) -> tuple:
    """
    Generate a summary and key terms for a page using LLM.
    
    Args:
        text: Page text
        llm_client: LLM client
        page_no: Page number
    
    Returns:
        Tuple of (summary, key_terms list)
    """
    try:
        # Create prompt for summary and key terms
        prompt = f"""You are analyzing a page from an educational slide deck.

Page content:
{text}

Your task:
Give me a detailed, beginner-friendly explanation of this page. 
Do NOT summarize it. 
Explain every idea clearly, break down complex terms, unpack hidden assumptions, and add simple real-life analogies where helpful. 
Your goal is to make me fully understand the page as if you're teaching me personally.

Format your response EXACTLY as follows (use these exact delimiters):

===SUMMARY_START===
Your detailed explanation here
===SUMMARY_END===

===KEY_TERMS_START===
term1
term2
term3
===KEY_TERMS_END===

Important: Put each key term on a separate line between the KEY_TERMS delimiters.
"""
        
        messages = [
            {"role": "system", "content": "You are a helpful teaching assistant."},
            {"role": "user", "content": prompt}
        ]
        
        # Stream and collect response
        full_response = ""
        async for token in llm_client.stream_chat(messages, temperature=0.3, max_tokens=2000):
            full_response += token
        
        # Parse delimited response instead of JSON
        import json
        summary = ""
        key_terms = []
        
        # Extract summary
        if "===SUMMARY_START===" in full_response and "===SUMMARY_END===" in full_response:
            summary_start = full_response.find("===SUMMARY_START===") + len("===SUMMARY_START===")
            summary_end = full_response.find("===SUMMARY_END===")
            summary = full_response[summary_start:summary_end].strip()
        else:
            # Fallback: try to find JSON format (for backward compatibility)
            json_match = full_response
            if "```json" in full_response:
                json_match = full_response.split("```json")[1].split("```")[0].strip()
            elif "```" in full_response:
                json_match = full_response.split("```")[1].split("```")[0].strip()
            
            try:
                result = json.loads(json_match)
                summary = result.get("summary", "")
                key_terms = result.get("key_terms", [])
            except json.JSONDecodeError:
                # If all parsing fails, use the full response as summary
                logger.warning(f"Could not parse response format for page {page_no}, using full response as summary")
                summary = full_response
        
        # Extract key terms if not already extracted
        if not key_terms and "===KEY_TERMS_START===" in full_response and "===KEY_TERMS_END===" in full_response:
            terms_start = full_response.find("===KEY_TERMS_START===") + len("===KEY_TERMS_START===")
            terms_end = full_response.find("===KEY_TERMS_END===")
            terms_text = full_response[terms_start:terms_end].strip()
            # Split by newlines and clean up
            key_terms = [term.strip() for term in terms_text.split("\n") if term.strip()]
        
        logger.debug(f"Generated summary and {len(key_terms)} key terms for page {page_no}")
        return summary, key_terms
        
    except Exception as e:
        logger.error(f"Error generating summary for page {page_no}: {e}")
        return "", []



