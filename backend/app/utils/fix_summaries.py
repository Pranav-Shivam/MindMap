"""
Utility to check for and regenerate missing page summaries.
"""
import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger
from ..config import config
from ..db import couch_client
from ..utils.llm import get_chat_client
import json


async def _generate_summary_and_terms(
    text: str,
    llm_client,
    page_no: int,
    doc_id: str
) -> tuple:
    """
    Generate a summary and key terms for a page using LLM.
    
    Args:
        text: Page text
        llm_client: LLM client
        page_no: Page number
        doc_id: Document ID
    
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
        summary = ""
        key_terms = []
        
        # Extract summary
        if "===SUMMARY_START===" in full_response and "===SUMMARY_END===" in full_response:
            summary_start = full_response.find("===SUMMARY_START===") + len("===SUMMARY_START===")
            summary_end = full_response.find("===SUMMARY_END===")
            summary = full_response[summary_start:summary_end].strip()
        else:
            # Fallback: try to find JSON format (for backward compatibility)
            import re
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
        
        logger.info(f"Generated summary ({len(summary)} chars) and {len(key_terms)} key terms for page {page_no} of doc {doc_id}")
        return summary, key_terms
        
    except Exception as e:
        logger.error(f"Error generating summary for page {page_no} of doc {doc_id}: {e}")
        logger.error(f"LLM response was: {full_response[:500] if 'full_response' in locals() else 'N/A'}")
        return "", []


async def check_missing_summaries(doc_id: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Check for pages with missing or empty summaries.
    
    Args:
        doc_id: Optional document ID to check. If None, checks all documents.
    
    Returns:
        Dictionary mapping doc_id to list of pages with missing summaries
    """
    logger.info(f"Checking for missing summaries{f' in document {doc_id}' if doc_id else ' across all documents'}")
    
    missing_summaries = {}
    
    try:
        # Get all page documents
        pages_db = couch_client.get_or_create_db(config.pages_db)
        
        for page_doc_id in pages_db:
            if page_doc_id.startswith('_design'):
                continue
            
            page_doc = pages_db.get(page_doc_id)
            if not page_doc or page_doc.get('type') != 'page':
                continue
            
            # Filter by document if specified
            current_doc_id = page_doc.get('document_id')
            if doc_id and current_doc_id != doc_id:
                continue
            
            # Check if summary is missing or empty
            summary = page_doc.get('summary', '').strip()
            text = page_doc.get('text', '').strip()
            
            # Only flag as missing if page has text but no summary
            if text and not summary:
                if current_doc_id not in missing_summaries:
                    missing_summaries[current_doc_id] = []
                
                missing_summaries[current_doc_id].append({
                    'page_no': page_doc.get('page_no'),
                    'page_id': page_doc_id,
                    'text_length': len(text),
                    'has_text': bool(text),
                    'has_summary': bool(summary)
                })
        
        # Log results
        total_missing = sum(len(pages) for pages in missing_summaries.values())
        logger.info(f"Found {total_missing} pages with missing summaries across {len(missing_summaries)} documents")
        
        for doc_id, pages in missing_summaries.items():
            logger.info(f"  Document {doc_id}: {len(pages)} pages missing summaries")
            for page in pages:
                logger.info(f"    Page {page['page_no']}: {page['text_length']} chars of text, no summary")
        
        return missing_summaries
        
    except Exception as e:
        logger.error(f"Error checking for missing summaries: {e}")
        raise


async def regenerate_summaries(
    doc_id: str,
    page_numbers: Optional[List[int]] = None,
    llm_provider: str = "gpt",
    llm_model: str = "gpt-4o-mini"
) -> Dict[str, Any]:
    """
    Regenerate summaries for specified pages or all pages with missing summaries.
    
    Args:
        doc_id: Document ID
        page_numbers: Optional list of specific page numbers to regenerate. 
                     If None, regenerates all pages with missing summaries.
        llm_provider: LLM provider to use
        llm_model: LLM model to use
    
    Returns:
        Dictionary with regeneration results
    """
    logger.info(f"Starting summary regeneration for document {doc_id}")
    
    try:
        # Get LLM client
        llm_client = get_chat_client(llm_provider, llm_model)
        
        # Get document to verify it exists
        doc = couch_client.get_doc(config.documents_db, doc_id)
        if not doc:
            raise ValueError(f"Document {doc_id} not found")
        
        # Determine which pages to process
        if page_numbers is not None:
            # Process specific pages
            pages_to_process = []
            for page_no in page_numbers:
                page_id = f"{doc_id}_page_{page_no}"
                page_doc = couch_client.get_doc(config.pages_db, page_id)
                if page_doc:
                    pages_to_process.append(page_doc)
                else:
                    logger.warning(f"Page {page_no} not found for document {doc_id}")
        else:
            # Find all pages with missing summaries for this document
            missing_summaries = await check_missing_summaries(doc_id)
            if doc_id not in missing_summaries:
                logger.info(f"No pages with missing summaries found for document {doc_id}")
                return {
                    "success": True,
                    "message": "No pages with missing summaries",
                    "pages_processed": 0,
                    "pages_updated": 0,
                    "pages_failed": 0
                }
            
            # Get full page documents
            pages_to_process = []
            for page_info in missing_summaries[doc_id]:
                page_doc = couch_client.get_doc(config.pages_db, page_info['page_id'])
                if page_doc:
                    pages_to_process.append(page_doc)
        
        logger.info(f"Processing {len(pages_to_process)} pages for document {doc_id}")
        
        # Process each page
        results = {
            "success": True,
            "pages_processed": 0,
            "pages_updated": 0,
            "pages_failed": 0,
            "details": []
        }
        
        for page_doc in pages_to_process:
            page_no = page_doc.get('page_no')
            page_id = page_doc.get('_id')
            text = page_doc.get('text', '').strip()
            
            results["pages_processed"] += 1
            
            try:
                if not text:
                    logger.warning(f"Page {page_no} has no text content, skipping")
                    results["details"].append({
                        "page_no": page_no,
                        "status": "skipped",
                        "reason": "No text content"
                    })
                    continue
                
                # Generate summary and key terms
                logger.info(f"Regenerating summary for page {page_no} (doc: {doc_id})")
                summary, key_terms = await _generate_summary_and_terms(
                    text,
                    llm_client,
                    page_no,
                    doc_id
                )
                
                if summary:
                    # Update the page document
                    update_success = couch_client.update_doc(
                        config.pages_db,
                        page_id,
                        {
                            "summary": summary,
                            "key_terms": key_terms
                        }
                    )
                    
                    if update_success:
                        results["pages_updated"] += 1
                        results["details"].append({
                            "page_no": page_no,
                            "status": "success",
                            "summary_length": len(summary),
                            "key_terms_count": len(key_terms)
                        })
                        logger.info(f"Successfully updated summary for page {page_no}")
                    else:
                        results["pages_failed"] += 1
                        results["details"].append({
                            "page_no": page_no,
                            "status": "failed",
                            "reason": "Failed to update document"
                        })
                        logger.error(f"Failed to update page {page_no} in database")
                else:
                    results["pages_failed"] += 1
                    results["details"].append({
                        "page_no": page_no,
                        "status": "failed",
                        "reason": "Failed to generate summary"
                    })
                    logger.error(f"Failed to generate summary for page {page_no}")
                    
            except Exception as e:
                results["pages_failed"] += 1
                results["details"].append({
                    "page_no": page_no,
                    "status": "failed",
                    "reason": str(e)
                })
                logger.error(f"Error processing page {page_no}: {e}")
        
        logger.info(f"Summary regeneration complete: {results['pages_updated']} updated, {results['pages_failed']} failed out of {results['pages_processed']} processed")
        return results
        
    except Exception as e:
        logger.error(f"Error regenerating summaries for document {doc_id}: {e}")
        raise


async def regenerate_all_missing_summaries(
    llm_provider: str = "gpt",
    llm_model: str = "gpt-4o-mini"
) -> Dict[str, Any]:
    """
    Regenerate summaries for all pages with missing summaries across all documents.
    
    Args:
        llm_provider: LLM provider to use
        llm_model: LLM model to use
    
    Returns:
        Dictionary with overall results
    """
    logger.info("Starting global summary regeneration for all documents")
    
    try:
        # Check for all missing summaries
        missing_summaries = await check_missing_summaries()
        
        if not missing_summaries:
            logger.info("No pages with missing summaries found")
            return {
                "success": True,
                "message": "No pages with missing summaries",
                "documents_processed": 0,
                "total_pages_updated": 0,
                "total_pages_failed": 0
            }
        
        # Process each document
        overall_results = {
            "success": True,
            "documents_processed": len(missing_summaries),
            "total_pages_updated": 0,
            "total_pages_failed": 0,
            "document_results": {}
        }
        
        for doc_id in missing_summaries.keys():
            logger.info(f"Processing document {doc_id}")
            
            try:
                result = await regenerate_summaries(
                    doc_id=doc_id,
                    page_numbers=None,  # Process all missing summaries
                    llm_provider=llm_provider,
                    llm_model=llm_model
                )
                
                overall_results["total_pages_updated"] += result["pages_updated"]
                overall_results["total_pages_failed"] += result["pages_failed"]
                overall_results["document_results"][doc_id] = result
                
            except Exception as e:
                logger.error(f"Error processing document {doc_id}: {e}")
                overall_results["document_results"][doc_id] = {
                    "success": False,
                    "error": str(e)
                }
        
        logger.info(f"Global summary regeneration complete: {overall_results['total_pages_updated']} pages updated across {overall_results['documents_processed']} documents")
        return overall_results
        
    except Exception as e:
        logger.error(f"Error in global summary regeneration: {e}")
        raise


if __name__ == "__main__":
    """Run as a standalone script to check and fix missing summaries."""
    import sys
    
    async def main():
        # Check for command line arguments
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "check":
                # Check for missing summaries
                doc_id = sys.argv[2] if len(sys.argv) > 2 else None
                missing = await check_missing_summaries(doc_id)
                
                if not missing:
                    print("No pages with missing summaries found.")
                else:
                    print(f"\nFound missing summaries in {len(missing)} documents:")
                    for doc_id, pages in missing.items():
                        print(f"\nDocument: {doc_id}")
                        print(f"  Pages missing summaries: {[p['page_no'] for p in pages]}")
            
            elif command == "fix":
                # Regenerate missing summaries
                doc_id = sys.argv[2] if len(sys.argv) > 2 else None
                llm_provider = sys.argv[3] if len(sys.argv) > 3 else "gpt"
                llm_model = sys.argv[4] if len(sys.argv) > 4 else "gpt-4o-mini"
                
                if doc_id:
                    print(f"Regenerating summaries for document {doc_id}...")
                    result = await regenerate_summaries(doc_id, None, llm_provider, llm_model)
                else:
                    print("Regenerating summaries for all documents...")
                    result = await regenerate_all_missing_summaries(llm_provider, llm_model)
                
                print(f"\nResults:")
                print(f"  Pages updated: {result.get('pages_updated', result.get('total_pages_updated', 0))}")
                print(f"  Pages failed: {result.get('pages_failed', result.get('total_pages_failed', 0))}")
            
            else:
                print(f"Unknown command: {command}")
                print("Usage:")
                print("  python -m backend.app.utils.fix_summaries check [doc_id]")
                print("  python -m backend.app.utils.fix_summaries fix [doc_id] [llm_provider] [llm_model]")
        else:
            print("Usage:")
            print("  python -m backend.app.utils.fix_summaries check [doc_id]")
            print("  python -m backend.app.utils.fix_summaries fix [doc_id] [llm_provider] [llm_model]")
    
    asyncio.run(main())

