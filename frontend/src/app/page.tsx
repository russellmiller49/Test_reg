import Link from 'next/link';
import { Box, Button, Typography } from '@mui/material';

export default function Home() {
  return (
    <Box sx={{ p: 6, maxWidth: 720 }}>
      <Typography variant="h4" gutterBottom>
        Bronchoscopy Registry
      </Typography>
      <Typography sx={{ mb: 3 }}>
        Capture structured annotation data for bronchoscopy procedures. Use the button below to create
        a new annotation.
      </Typography>
      <Button component={Link} href="/annotations/new">
        New Annotation
      </Button>
    </Box>
  );
}
