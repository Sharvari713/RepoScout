import React, { useState } from 'react';
import {
  Container,
  TextField,
  Button,
  Grid,
  Card,
  CardContent,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  ToggleButton,
  ToggleButtonGroup,
  Box,
  CircularProgress
} from '@mui/material';
import { GitHub as GitHubIcon, Search as SearchIcon } from '@mui/icons-material';
import axios from 'axios';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const API_BASE_URL = 'http://localhost:5000/api';

function App() {
  const [searchType, setSearchType] = useState('url');
  const [searchInput, setSearchInput] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedRepo, setSelectedRepo] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const handleSearchTypeChange = (event, newType) => {
    if (newType !== null) {
      setSearchType(newType);
    }
  };

  const handleSearch = async () => {
    if (!searchInput.trim()) {
      toast.error('Please enter a search term');
      return;
    }

    setLoading(true);
    try {
      let endpoint = '';
      let payload = {};

      if (searchType === 'url') {
        endpoint = '/related-repos';
        payload = { url: searchInput };
      } else {
        endpoint = '/search-by-topic';
        payload = { topic: searchInput };
      }

      const response = await axios.post(`${API_BASE_URL}${endpoint}`, payload);
      setResults(response.data.data);
    } catch (error) {
      toast.error(error.response?.data?.error || 'An error occurred');
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCardClick = async (repo) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/repo-metadata`, {
        url: repo.url
      });
      setSelectedRepo(response.data.data);
      setDialogOpen(true);
    } catch (error) {
      toast.error('Failed to fetch detailed information');
    }
  };

  const ResultCard = ({ repo }) => (
    <Card 
      sx={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        cursor: 'pointer',
        '&:hover': {
          boxShadow: 6
        }
      }}
      onClick={() => handleCardClick(repo)}
    >
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {repo.name}
        </Typography>
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          by {repo.owner}
        </Typography>
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Stars: {repo.stars}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Forks: {repo.forks}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Activity Score: {repo.activity}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <ToastContainer />
      
      {/* Search Section */}
      <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', gap: 2 }}>
        <ToggleButtonGroup
          value={searchType}
          exclusive
          onChange={handleSearchTypeChange}
          aria-label="search type"
        >
          <ToggleButton value="url" aria-label="search by url">
            <GitHubIcon sx={{ mr: 1 }} />
            Repository URL
          </ToggleButton>
          <ToggleButton value="topic" aria-label="search by topic">
            <SearchIcon sx={{ mr: 1 }} />
            Topic
          </ToggleButton>
        </ToggleButtonGroup>

        <TextField
          fullWidth
          variant="outlined"
          placeholder={searchType === 'url' ? 'Enter GitHub repository URL' : 'Enter search topic'}
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
        />

        <Button
          variant="contained"
          onClick={handleSearch}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : <SearchIcon />}
        >
          Search
        </Button>
      </Box>

      {/* Results Section */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3}>
          {results.map((repo, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <ResultCard repo={repo} />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Detailed View Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedRepo && (
          <>
            <DialogTitle>
              {selectedRepo['Repository Name']}
              <Typography variant="subtitle1" color="text.secondary">
                by {selectedRepo.Owner}
              </Typography>
            </DialogTitle>
            <DialogContent dividers>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <Typography variant="body1" paragraph>
                    {selectedRepo.Description}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2">Stars</Typography>
                  <Typography variant="body2">{selectedRepo.Stars}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2">Forks</Typography>
                  <Typography variant="body2">{selectedRepo.Forks}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2">Open Issues</Typography>
                  <Typography variant="body2">{selectedRepo['Open Issues']}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2">Primary Language</Typography>
                  <Typography variant="body2">{selectedRepo['Primary Language']}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2">Created At</Typography>
                  <Typography variant="body2">{selectedRepo['Created At']}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2">Updated At</Typography>
                  <Typography variant="body2">{selectedRepo['Updated At']}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2">License</Typography>
                  <Typography variant="body2">{selectedRepo.License}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2">Topics</Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {selectedRepo.Topics.map((topic, index) => (
                      <Typography
                        key={index}
                        variant="body2"
                        sx={{
                          bgcolor: 'primary.main',
                          color: 'white',
                          px: 1,
                          py: 0.5,
                          borderRadius: 1
                        }}
                      >
                        {topic}
                      </Typography>
                    ))}
                  </Box>
                </Grid>
              </Grid>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDialogOpen(false)}>Close</Button>
              <Button
                variant="contained"
                href={selectedRepo['Clone URL']}
                target="_blank"
                rel="noopener noreferrer"
              >
                View on GitHub
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Container>
  );
}

export default App; 