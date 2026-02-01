import { useState, useEffect } from 'react';
import { Document, Page } from 'react-pdf';
import { pagesApi, documentsApi } from '@/lib/api';
import { Button } from './ui/button';
import { ZoomIn, ZoomOut, RotateCw, RotateCcw, Undo2 } from 'lucide-react';
import { motion } from 'framer-motion';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

function PDFViewer({ docId, currentPage, pages, onPageChange }) {
  const [scale, setScale] = useState(1.0);
  const [rotation, setRotation] = useState(0); // Rotation in degrees (0, 90, 180, 270)
  const [numPages, setNumPages] = useState(null);
  const [previewUrls, setPreviewUrls] = useState({});
  const [thumbPages, setThumbPages] = useState(pages);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [hasMorePages, setHasMorePages] = useState(true);
  const [mainDocumentUrl, setMainDocumentUrl] = useState(null);
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8005';

  const handleZoomIn = () => setScale((s) => Math.min(s + 0.2, 3.0));
  const handleZoomOut = () => setScale((s) => Math.max(s - 0.2, 0.5));

  const handleRotateLeft = () => {
    setRotation((r) => (r - 90 + 360) % 360);
  };

  const handleRotateRight = () => {
    setRotation((r) => (r + 90) % 360);
  };

  const handleResetRotation = () => {
    setRotation(0);
  };

  // Reset rotation when page changes (optional - remove if you want rotation to persist)
  useEffect(() => {
    setRotation(0);
  }, [currentPage]);

  // Load preview images for thumbnails
  // Keep a local copy of pages (so we can append on scroll)
  useEffect(() => {
    setThumbPages(pages);
    setHasMorePages(true);
    // clear preview urls when source pages change
    Object.values(previewUrls).forEach(url => URL.revokeObjectURL(url));
    setPreviewUrls({});
  }, [docId, pages]);

  // Load preview images for thumbnails (only for pages that don't yet have a preview)
  useEffect(() => {
    let mounted = true;
    const createdUrls = [];

    const loadPreviews = async () => {
      for (const page of thumbPages) {
        if (!mounted) return;
        if (previewUrls[page.page_no]) continue; // already loaded
        try {
          const response = await pagesApi.getPreview(docId, page.page_no);
          const blob = response.data;
          const url = URL.createObjectURL(blob);
          createdUrls.push(url);
          setPreviewUrls((prev) => ({ ...prev, [page.page_no]: url }));
        } catch (error) {
          console.error(`Failed to load preview for page ${page.page_no}:`, error);
        }
      }
    };

    if (thumbPages.length > 0) {
      loadPreviews();
    }

    return () => {
      mounted = false;
      // revoke only URLs created in this effect
      createdUrls.forEach((u) => URL.revokeObjectURL(u));
    };
  }, [docId, thumbPages]);

  // Load main document PDF
  useEffect(() => {
    const loadMainDocument = async () => {
      try {
        const response = await documentsApi.getPdf(docId);
        const blob = response.data;
        const url = URL.createObjectURL(blob);

        // Cleanup previous URL
        if (mainDocumentUrl) {
          URL.revokeObjectURL(mainDocumentUrl);
        }

        setMainDocumentUrl(url);
      } catch (error) {
        console.error(`Failed to load main document:`, error);
      }
    };

    loadMainDocument();

    // Cleanup URL when component unmounts or docId changes
    return () => {
      if (mainDocumentUrl) {
        URL.revokeObjectURL(mainDocumentUrl);
      }
    };
  }, [docId]);

  const loadOnScrollToBottom = (e) => {
    const { scrollTop, scrollHeight, clientHeight } = e.target;
    if (scrollTop + clientHeight >= scrollHeight - 10 && !isLoadingMore && hasMorePages) {
      (async () => {
        setIsLoadingMore(true);
        try {
          const offset = thumbPages.length;
          const limit = 50;
          const resp = await pagesApi.list(docId, offset, limit);
          const newPages = resp.data;
          if (Array.isArray(newPages) && newPages.length > 0) {
            setThumbPages((prev) => [...prev, ...newPages]);
          }
          if (!Array.isArray(newPages) || newPages.length < limit) {
            setHasMorePages(false);
          }
        } catch (err) {
          console.error('Failed to load more pages:', err);
        } finally {
          setIsLoadingMore(false);
        }
      })();
    }
  };

  return (
    <div className="flex h-full flex-col bg-background">
      {/* Controls */}
      <div className="flex items-center gap-2 border-b bg-background p-2 flex-wrap">
        {/* Zoom Controls */}
        <div className="flex items-center gap-1 border-r pr-2 mr-2">
          <Button variant="ghost" size="sm" onClick={handleZoomOut} className="h-8 w-8 p-0">
            <ZoomOut className="h-4 w-4" />
          </Button>
          <span className="text-sm min-w-[3rem] text-center">{Math.round(scale * 100)}%</span>
          <Button variant="ghost" size="sm" onClick={handleZoomIn} className="h-8 w-8 p-0">
            <ZoomIn className="h-4 w-4" />
          </Button>
        </div>

        {/* Rotation Controls */}
        <div className="flex items-center gap-1 border-r pr-2 mr-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRotateLeft}
            className="h-8 w-8 p-0"
            title="Rotate counterclockwise"
          >
            <RotateCcw className="h-4 w-4" />
          </Button>
          <span className="text-xs text-muted-foreground min-w-[2.5rem] text-center">
            {rotation}°
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRotateRight}
            className="h-8 w-8 p-0"
            title="Rotate clockwise"
          >
            <RotateCw className="h-4 w-4" />
          </Button>
          {rotation !== 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleResetRotation}
              className="h-8 w-8 p-0 ml-1"
              title="Reset rotation"
            >
              <Undo2 className="h-3 w-3" />
            </Button>
          )}
        </div>
      </div>

      {/* PDF Display */}
      <div className="flex flex-1 overflow-hidden">
        {/* Thumbnails */}
        <div className="w-32 overflow-y-auto border-r bg-background p-2" onScroll={loadOnScrollToBottom}>
          {thumbPages.map((page) => (
            <div
              key={page.page_no}
              onClick={() => onPageChange(page.page_no)}
              className={`mb-2 cursor-pointer rounded border-2 p-1 transition-colors ${page.page_no === currentPage
                  ? 'border-primary'
                  : 'border-transparent hover:border-border'
                }`}
            >
              {previewUrls[page.page_no] ? (
                <img
                  src={previewUrls[page.page_no]}
                  alt={`Page ${page.page_no + 1}`}
                  className="w-full"
                />
              ) : (
                <div className="w-full h-20 bg-muted flex items-center justify-center text-xs text-muted-foreground rounded">
                  Loading...
                </div>
              )}
              <div className="mt-1 text-center text-xs">{page.page_no + 1}</div>
            </div>
          ))}
          {isLoadingMore && (
            <div className="py-2 text-center text-xs text-muted-foreground">Loading more...</div>
          )}
        </div>

        {/* Main Page View */}
        <div className="flex-1 overflow-auto p-4">
          <div className="flex justify-center items-center min-h-full">
            {mainDocumentUrl ? (
              <motion.div
                key={`${currentPage}-${rotation}`}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.2 }}
              >
                <Document
                  file={mainDocumentUrl}
                  onLoadSuccess={({ numPages }) => setNumPages(numPages)}
                >
                  <Page
                    pageNumber={currentPage + 1}
                    scale={scale}
                    rotate={rotation}
                    renderTextLayer={true}
                    renderAnnotationLayer={false}
                    className="transition-transform duration-200"
                  />
                </Document>
              </motion.div>
            ) : (
              <div className="w-full h-96 bg-muted flex items-center justify-center rounded-lg">
                <div className="text-muted-foreground">Loading document...</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default PDFViewer;

