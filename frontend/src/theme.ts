import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    primary: {
      main: '#005A9C'
    },
    secondary: {
      main: '#FF6F3C'
    }
  },
  typography: {
    h5: {
      fontWeight: 600
    }
  },
  components: {
    MuiButton: {
      defaultProps: {
        variant: 'contained'
      }
    }
  }
});
