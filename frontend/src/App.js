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
  CircularProgress,
  Paper,
  Chip
} from '@mui/material';
import { GitHub as GitHubIcon, Search as SearchIcon } from '@mui/icons-material';
import axios from 'axios';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import RepoList from './components/RepoList';

const API_BASE_URL = 'http://localhost:5000/api';

function App() {
  const [searchType, setSearchType] = useState('url');
  const [searchInput, setSearchInput] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedRepo, setSelectedRepo] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [error, setError] = useState(null);

  const handleSearchTypeChange = (event, newType) => {
    if (newType !== null) {
      setSearchType(newType);
    }
  };

  const handleSearch = async () => {
    setLoading(true);
    setError(null);
    setSearchResults(null);

    try {
      let endpoint = '';
      let payload = {};

      if (searchType === 'url') {
        endpoint = 'http://localhost:5000/api/search';
        payload = { github_url: searchInput };
      } else {
        endpoint = 'http://localhost:5000/api/topic-search';
        payload = { topic: searchInput };
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch data');
      }

      const data = await response.json();
      setSearchResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCardClick = async (repo) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/metadata`, {
        github_url: repo.url
      });
      setSelectedRepo(response.data);
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
    <Container maxWidth="lg">
      <ToastContainer />
      
      <Box sx={{ my: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom align="center">
          RepoScout
        </Typography>
        <Typography variant="h6" component="h2" gutterBottom align="center" color="text.secondary">
          Discover and analyze GitHub repositories
        </Typography>

        <Paper elevation={3} sx={{ p: 3, mt: 4 }}>
          <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
            <Button
              variant={searchType === 'url' ? 'contained' : 'outlined'}
              onClick={() => setSearchType('url')}
            >
              Search by URL
            </Button>
            <Button
              variant={searchType === 'topic' ? 'contained' : 'outlined'}
              onClick={() => setSearchType('topic')}
            >
              Search by Topic
            </Button>
          </Box>

          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              fullWidth
              label={searchType === 'url' ? 'GitHub Repository URL' : 'Search Topic'}
              variant="outlined"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder={searchType === 'url' ? 'https://github.com/username/repo' : 'Enter a topic...'}
            />
            <Button
              variant="contained"
              onClick={handleSearch}
              disabled={!searchInput || loading}
            >
              Search
            </Button>
          </Box>
        </Paper>

        {error && (
          <Typography color="error" sx={{ mt: 2 }}>
            Error: {error}
          </Typography>
        )}

        <RepoList 
          searchResults={searchResults} 
          loading={loading} 
          onCardClick={handleCardClick}
        />
      </Box>

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
                      <Chip
                        key={index}
                        label={topic}
                        size="small"
                      />
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