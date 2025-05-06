import React, { useState } from 'react';
import { Card, CardContent, Typography, Grid, Chip, Box, CircularProgress, TextField, Button, Alert, LinearProgress } from '@mui/material';
import { Star, ForkRight, Code, HealthAndSafety } from '@mui/icons-material';

const RepoList = ({ searchResults, loading, onCardClick }) => {
  const [profileText, setProfileText] = useState('');
  const [mostSimilarRepo, setMostSimilarRepo] = useState(null);
  const [similarityScores, setSimilarityScores] = useState(null);
  const [error, setError] = useState(null);

  const handleProfileSubmit = async () => {
    if (!profileText.trim()) return;
    
    try {
      setError(null);
      const response = await fetch('http://localhost:5000/api/match-profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          profile: profileText,
          repositories: searchResults.repositories
        }),
      });

      if (!response.ok) throw new Error('Failed to match profile');
      
      const data = await response.json();
      setMostSimilarRepo(data.most_similar_repo);
      setSimilarityScores(data.debug_info.all_scores);
    } catch (error) {
      setError(error.message);
      console.error('Error matching profile:', error);
    }
  };

  const SimilarityScore = ({ score, label }) => (
    <Box sx={{ mb: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
        <Typography variant="caption" color="text.secondary">
          {label}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {(score * 100).toFixed(1)}%
        </Typography>
      </Box>
      <LinearProgress 
        variant="determinate" 
        value={score * 100} 
        sx={{ 
          height: 4,
          borderRadius: 2,
          backgroundColor: 'grey.200',
          '& .MuiLinearProgress-bar': {
            backgroundColor: score > 0.7 ? 'success.main' : score > 0.4 ? 'warning.main' : 'error.main'
          }
        }}
      />
    </Box>
  );

  const HealthScore = ({ score }) => {
    const getHealthColor = (score) => {
      if (score >= 80) return 'success.main';
      if (score >= 60) return 'warning.main';
      return 'error.main';
    };

    return (
      <Box sx={{ mb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
          <HealthAndSafety sx={{ fontSize: 16 }} />
          <Typography variant="caption" color="text.secondary">
            Health Score
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
            {score.toFixed(1)}%
          </Typography>
        </Box>
        <LinearProgress 
          variant="determinate" 
          value={score} 
          sx={{ 
            height: 4,
            borderRadius: 2,
            backgroundColor: 'grey.200',
            '& .MuiLinearProgress-bar': {
              backgroundColor: getHealthColor(score)
            }
          }}
        />
      </Box>
    );
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (!searchResults || !searchResults.repositories) {
    return null;
  }

  const repositories = searchResults.repositories;

  return (
    <Box sx={{ mt: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Tell us about yourself
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Describe your interests, skills, and what you're looking for (max 80 words)
        </Typography>
        <TextField
          fullWidth
          multiline
          rows={3}
          value={profileText}
          onChange={(e) => setProfileText(e.target.value)}
          placeholder="I'm interested in web development, particularly React and Node.js. I have experience with full-stack development and am looking for projects that focus on user experience and modern design patterns..."
          sx={{ mb: 2 }}
        />
        <Button 
          variant="contained" 
          onClick={handleProfileSubmit}
          disabled={!profileText.trim()}
        >
          Find Matching Repositories
        </Button>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
      </Box>

      <Grid container spacing={3}>
        {repositories.map((repo) => {
          const repoScore = similarityScores?.find(s => s.repo_name === repo.name);
          
          return (
            <Grid item xs={12} sm={6} md={4} key={repo.url}>
              <Card 
                sx={{ 
                  height: '100%', 
                  cursor: 'pointer',
                  '&:hover': {
                    boxShadow: 6
                  },
                  ...(mostSimilarRepo && mostSimilarRepo.url === repo.url && {
                    border: '2px solid #1976d2',
                    animation: 'highlight 2s ease-in-out',
                    '@keyframes highlight': {
                      '0%': {
                        transform: 'scale(1)',
                        boxShadow: '0 0 0 0 rgba(25, 118, 210, 0.4)'
                      },
                      '50%': {
                        transform: 'scale(1.02)',
                        boxShadow: '0 0 0 10px rgba(25, 118, 210, 0)'
                      },
                      '100%': {
                        transform: 'scale(1)',
                        boxShadow: '0 0 0 0 rgba(25, 118, 210, 0)'
                      }
                    }
                  })
                }}
                onClick={() => onCardClick(repo)}
              >
                <CardContent>
                  <Typography variant="h6" component="div" gutterBottom>
                    {repo.owner}/{repo.name}
                  </Typography>

                  <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                    <Chip
                      icon={<Star />}
                      label={`${repo.stars} stars`}
                      size="small"
                    />
                    <Chip
                      icon={<ForkRight />}
                      label={`${repo.forks} forks`}
                      size="small"
                    />
                    {repo.language && (
                      <Chip
                        icon={<Code />}
                        label={repo.language}
                        size="small"
                      />
                    )}
                  </Box>

                  <HealthScore score={repo.health_score} />

                  {repoScore && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Match Score: {(repoScore.score * 100).toFixed(1)}%
                      </Typography>
                      <SimilarityScore 
                        score={repoScore.field_scores.description} 
                        label="Description Match" 
                      />
                      <SimilarityScore 
                        score={repoScore.field_scores.topics} 
                        label="Topics Match" 
                      />
                      <SimilarityScore 
                        score={repoScore.field_scores.language} 
                        label="Language Match" 
                      />
                      <SimilarityScore 
                        score={repoScore.field_scores.name} 
                        label="Name Match" 
                      />
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
};

export default RepoList; 