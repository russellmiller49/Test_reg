'use client';

import React from 'react';
import { Box, Snackbar, Alert } from '@mui/material';
import ProcedureAnnotationForm from '@/components/forms/ProcedureAnnotationForm';
import { AnnotationFormData } from '@/types/procedure';
import { saveAnnotation } from '@/lib/api';

export default function NewAnnotationPage() {
  const [saving, setSaving] = React.useState(false);
  const [snackbar, setSnackbar] = React.useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success'
  });

  const handleSubmit = async (data: AnnotationFormData) => {
    setSaving(true);
    try {
      await saveAnnotation(data);
      setSnackbar({ open: true, message: 'Annotation saved', severity: 'success' });
      setTimeout(() => {
        window.location.href = '/annotations';
      }, 600);
    } catch (error) {
      setSnackbar({
        open: true,
        message: error instanceof Error ? error.message : 'Failed to save annotation',
        severity: 'error'
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box sx={{ p: 4 }}>
      <ProcedureAnnotationForm onSubmit={handleSubmit} submitting={saving} />
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar((prev) => ({ ...prev, open: false }))}
      >
        <Alert
          severity={snackbar.severity}
          onClose={() => setSnackbar((prev) => ({ ...prev, open: false }))}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
