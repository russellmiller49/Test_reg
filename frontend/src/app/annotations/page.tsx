import Link from 'next/link';
import { Box, Button, Typography } from '@mui/material';

export default function AnnotationListPage() {
  return (
    <Box sx={{ p: 6 }}>
      <Typography variant="h4" gutterBottom>
        Annotations
      </Typography>
      <Typography sx={{ mb: 3 }}>
        Annotation records will appear here. Use the button below to record a new procedure.
      </Typography>
      <Button component={Link} href="/annotations/new">
        New Annotation
      </Button>
    </Box>
  );
}
