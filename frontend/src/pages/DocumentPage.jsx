import { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { documentsApi, pagesApi } from '@/lib/api';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import PDFViewer from '@/components/PDFViewer';
import StudyPanel from '@/components/StudyPanel';
import Header from '@/components/Header';
import { motion, AnimatePresence } from 'framer-motion';

function DocumentPage() {
  const { docId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState('pdf'); // 'pdf' or 'study'
  const pageNo = parseInt(searchParams.get('page') || '0');

  // Fetch document
  const { data: document } = useQuery({
    queryKey: ['document', docId],
    queryFn: async () => {
      const { data } = await documentsApi.get(docId);
      return data;
    },
  });

  // Fetch pages list
  const { data: pages = [] } = useQuery({
    queryKey: ['pages', docId],
    queryFn: async () => {
      const { data } = await pagesApi.list(docId);
      return data;
    },
  });

  // Fetch current page details
  const { data: pageData } = useQuery({
    queryKey: ['page', docId, pageNo],
    queryFn: async () => {
      const { data } = await pagesApi.get(docId, pageNo);
      return data;
    },
    enabled: !!pages.find(p => p.page_no === pageNo && p.ready),
  });

  const handlePageChange = (newPageNo) => {
    setSearchParams({ page: newPageNo });
  };

  return (
    <motion.div
      className="flex h-screen flex-col bg-background"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <Header document={document} currentPage={pageNo} onPageChange={handlePageChange} />
      
      {/* Mobile Tabs */}
      <div className="md:hidden flex border-b bg-background/95 backdrop-blur-sm">
        <button
          onClick={() => setActiveTab('pdf')}
          className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${
            activeTab === 'pdf'
              ? 'border-b-2 border-primary text-primary bg-primary/5'
              : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
          }`}
        >
          Document
        </button>
        <button
          onClick={() => setActiveTab('study')}
          className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${
            activeTab === 'study'
              ? 'border-b-2 border-primary text-primary bg-primary/5'
              : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
          }`}
        >
          Study
        </button>
      </div>

      {/* Desktop Layout */}
      <div className="hidden md:flex flex-1 overflow-hidden">
        <PanelGroup direction="horizontal">
          <Panel defaultSize={50} minSize={30}>
            <PDFViewer
              docId={docId}
              currentPage={pageNo}
              pages={pages}
              onPageChange={handlePageChange}
            />
          </Panel>
          
          <PanelResizeHandle className="w-2 bg-border hover:bg-primary transition-colors" />
          
          <Panel defaultSize={50} minSize={30}>
            <StudyPanel
              docId={docId}
              pageNo={pageNo}
              pageData={pageData}
            />
          </Panel>
        </PanelGroup>
      </div>

      {/* Mobile Layout */}
      <div className="md:hidden flex-1 overflow-hidden">
        <AnimatePresence mode="wait">
          {activeTab === 'pdf' ? (
            <motion.div
              key="pdf-viewer"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              <PDFViewer
                docId={docId}
                currentPage={pageNo}
                pages={pages}
                onPageChange={handlePageChange}
              />
            </motion.div>
          ) : (
            <motion.div
              key="study-panel"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              <StudyPanel
                docId={docId}
                pageNo={pageNo}
                pageData={pageData}
              />
            </motion.div>
          )}
        </AnimatePresence>
    </div>
    </motion.div>
  );
}

export default DocumentPage;

