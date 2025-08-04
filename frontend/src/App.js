import React, { useState, useEffect, createContext, useContext } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Auth Context
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      fetchCurrentUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchCurrentUser = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        logout();
      }
    } catch (error) {
      console.error('Error fetching user:', error);
      logout();
    }
    setLoading(false);
  };

  const login = async (email, password) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        setToken(data.access_token);
        setUser(data.user);
        return { success: true };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail };
      }
    } catch (error) {
      return { success: false, error: 'Login failed' };
    }
  };

  const register = async (email, password, name) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password, name }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        setToken(data.access_token);
        setUser(data.user);
        return { success: true };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail };
      }
    } catch (error) {
      return { success: false, error: 'Registration failed' };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Auth Components
const AuthForm = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = isLogin 
      ? await login(formData.email, formData.password)
      : await register(formData.email, formData.password, formData.name);

    if (!result.success) {
      setError(result.error);
    }
    setLoading(false);
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>♠️ Poker League ♠️</h1>
          <p>{isLogin ? 'Sign in to your account' : 'Create your account'}</p>
        </div>
        
        <form onSubmit={handleSubmit} className="auth-form">
          {!isLogin && (
            <div className="form-group">
              <label>Full Name</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                placeholder="Enter your full name"
              />
            </div>
          )}
          
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              placeholder="Enter your email"
            />
          </div>
          
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              placeholder="Enter your password"
            />
          </div>

          {error && <div className="error-message">{error}</div>}
          
          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? '⏳ Processing...' : (isLogin ? '🚀 Sign In' : '✨ Create Account')}
          </button>
        </form>
        
        <div className="auth-switch">
          <span>
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button
              type="button"
              onClick={() => setIsLogin(!isLogin)}
              className="switch-button"
            >
              {isLogin ? 'Sign Up' : 'Sign In'}
            </button>
          </span>
        </div>
      </div>
    </div>
  );
};

// Dashboard Components
const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('my-leagues');
  const [myLeagues, setMyLeagues] = useState([]);
  const [allLeagues, setAllLeagues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedLeague, setSelectedLeague] = useState(null);
  const { user, token, logout } = useAuth();

  useEffect(() => {
    fetchLeagues();
  }, []);

  const fetchLeagues = async () => {
    try {
      const [myResponse, allResponse] = await Promise.all([
        fetch(`${BACKEND_URL}/api/leagues/my`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${BACKEND_URL}/api/leagues`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      if (myResponse.ok && allResponse.ok) {
        const myData = await myResponse.json();
        const allData = await allResponse.json();
        setMyLeagues(myData);
        setAllLeagues(allData.filter(league => 
          !myData.some(myLeague => myLeague.id === league.id)
        ));
      }
    } catch (error) {
      console.error('Error fetching leagues:', error);
    }
    setLoading(false);
  };

  const handleJoinLeague = async (leagueId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/leagues/join`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ league_id: leagueId })
      });

      if (response.ok) {
        fetchLeagues(); // Refresh leagues
      } else {
        const error = await response.json();
        alert(error.detail);
      }
    } catch (error) {
      console.error('Error joining league:', error);
    }
  };

  if (selectedLeague) {
    return <GameInterface league={selectedLeague} onBack={() => setSelectedLeague(null)} />;
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>♠️ Poker League Dashboard</h1>
          <p>Welcome back, {user.name}! {user.avatar}</p>
        </div>
        <div className="header-right">
          <button onClick={() => setShowCreateForm(true)} className="create-league-btn">
            ➕ Create League
          </button>
          <button onClick={logout} className="logout-btn">
            🚪 Logout
          </button>
        </div>
      </header>

      <div className="dashboard-tabs">
        <button
          className={`tab ${activeTab === 'my-leagues' ? 'active' : ''}`}
          onClick={() => setActiveTab('my-leagues')}
        >
          🏆 My Leagues ({myLeagues.length})
        </button>
        <button
          className={`tab ${activeTab === 'browse' ? 'active' : ''}`}
          onClick={() => setActiveTab('browse')}
        >
          🔍 Browse Leagues ({allLeagues.length})
        </button>
        <button
          className={`tab ${activeTab === 'leaderboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('leaderboard')}
        >
          📊 Leaderboard
        </button>
        <button
          className={`tab ${activeTab === 'my-stats' ? 'active' : ''}`}
          onClick={() => setActiveTab('my-stats')}
        >
          📈 My Stats
        </button>
      </div>

      <div className="dashboard-content">
        {loading ? (
          <div className="loading">
            <div className="loading-spinner"></div>
            <p>Loading...</p>
          </div>
        ) : (
          <>
            {activeTab === 'my-leagues' && (
              <LeagueGrid 
                leagues={myLeagues} 
                isMyLeagues={true}
                onSelectLeague={setSelectedLeague}
              />
            )}
            {activeTab === 'browse' && (
              <LeagueGrid 
                leagues={allLeagues} 
                isMyLeagues={false}
                onJoinLeague={handleJoinLeague}
              />
            )}
            {activeTab === 'leaderboard' && <Leaderboard />}
            {activeTab === 'my-stats' && <MyStats />}
          </>
        )}
      </div>

      {showCreateForm && (
        <CreateLeagueModal 
          onClose={() => setShowCreateForm(false)}
          onSuccess={fetchLeagues}
        />
      )}
    </div>
  );
};

const LeagueGrid = ({ leagues, isMyLeagues, onSelectLeague, onJoinLeague }) => {
  if (leagues.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">🃏</div>
        <h3>{isMyLeagues ? 'No Leagues Yet' : 'No Available Leagues'}</h3>
        <p>
          {isMyLeagues 
            ? 'Create your first league or join an existing one'
            : 'All available leagues have been joined'
          }
        </p>
      </div>
    );
  }

  return (
    <div className="leagues-grid">
      {leagues.map(league => (
        <div key={league.id} className="league-card">
          <div className="league-header">
            <h3>{league.name}</h3>
            <span className="buy-in">${league.buy_in}</span>
          </div>
          
          <div className="league-info">
            <p className="description">{league.description || 'No description'}</p>
            <div className="league-meta">
              <span>👥 {league.member_count}/{league.max_players}</span>
              <span>🎮 {league.game_format}</span>
              <span>👑 {league.admin_name}</span>
            </div>
          </div>
          
          <div className="league-actions">
            {isMyLeagues ? (
              <button 
                onClick={() => onSelectLeague(league)}
                className="play-button"
              >
                🎯 Enter Game Room
              </button>
            ) : (
              <button 
                onClick={() => onJoinLeague(league.id)}
                className="join-button"
                disabled={league.member_count >= league.max_players}
              >
                {league.member_count >= league.max_players ? '🔒 Full' : '➕ Join League'}
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

const Leaderboard = () => {
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const { token } = useAuth();

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  const fetchLeaderboard = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/leaderboard`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setLeaderboard(data);
      }
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner"></div>
        <p>Loading leaderboard...</p>
      </div>
    );
  }

  if (leaderboard.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">🏆</div>
        <h3>No Games Played Yet</h3>
        <p>Complete some tournament games to see the leaderboard</p>
      </div>
    );
  }

  return (
    <div className="leaderboard-container">
      <div className="leaderboard-header">
        <h2>🏆 Overall Leaderboard</h2>
        <p>Rankings across all leagues and tournaments</p>
      </div>
      
      <div className="leaderboard-table">
        <div className="table-header">
          <div className="rank-col">Rank</div>
          <div className="player-col">Player</div>
          <div className="points-col">Points</div>
          <div className="games-col">Games</div>
          <div className="wins-col">Wins</div>
          <div className="winrate-col">Win Rate</div>
          <div className="earnings-col">Earnings</div>
        </div>
        
        {leaderboard.map((entry, index) => (
          <div key={entry.user_id} className={`table-row ${index < 3 ? 'top-three' : ''}`}>
            <div className="rank-col">
              <span className={`rank rank-${index + 1}`}>
                {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `#${entry.rank}`}
              </span>
            </div>
            <div className="player-col">
              <span className="player-avatar">{entry.user_avatar}</span>
              <span className="player-name">{entry.user_name}</span>
            </div>
            <div className="points-col">{entry.total_points}</div>
            <div className="games-col">{entry.games_played}</div>
            <div className="wins-col">{entry.wins}</div>
            <div className="winrate-col">{entry.win_rate}%</div>
            <div className="earnings-col">${entry.total_earnings}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

const MyStats = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const { user, token } = useAuth();

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/stats/user/${user.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner"></div>
        <p>Loading your stats...</p>
      </div>
    );
  }

  if (!stats || stats.stats.total_games === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📈</div>
        <h3>No Games Played Yet</h3>
        <p>Join some tournaments to start building your poker stats!</p>
      </div>
    );
  }

  return (
    <div className="stats-container">
      <div className="stats-header">
        <h2>📈 Your Poker Stats</h2>
        <div className="player-info">
          <span className="player-avatar-large">{user.avatar}</span>
          <span className="player-name-large">{user.name}</span>
        </div>
      </div>
      
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">🏆</div>
          <div className="stat-value">{stats.stats.total_points}</div>
          <div className="stat-label">Total Points</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">🎮</div>
          <div className="stat-value">{stats.stats.total_games}</div>
          <div className="stat-label">Games Played</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">🥇</div>
          <div className="stat-value">{stats.stats.total_wins}</div>
          <div className="stat-label">Wins</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">📊</div>
          <div className="stat-value">{stats.stats.win_rate}%</div>
          <div className="stat-label">Win Rate</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">🎯</div>
          <div className="stat-value">{stats.stats.avg_finish}</div>
          <div className="stat-label">Avg Finish</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-icon">💰</div>
          <div className="stat-value">${stats.stats.total_earnings}</div>
          <div className="stat-label">Total Earnings</div>
        </div>
      </div>
      
      {stats.recent_games.length > 0 && (
        <div className="recent-games">
          <h3>Recent Games</h3>
          <div className="games-list">
            {stats.recent_games.map((game, index) => (
              <div key={game.game_id} className="game-item">
                <div className="game-info">
                  <div className="league-name">{game.league_name}</div>
                  <div className="game-date">
                    {new Date(game.created_at).toLocaleDateString()}
                  </div>
                </div>
                <div className="game-result">
                  <div className={`finish-position ${game.finish_position === 1 ? 'winner' : ''}`}>
                    {game.finish_position === 1 ? '🥇' : `#${game.finish_position}`}
                  </div>
                  <div className="points-earned">+{game.points_earned} pts</div>
                  <div className={`earnings ${game.earnings >= 0 ? 'positive' : 'negative'}`}>
                    {game.earnings >= 0 ? '+' : ''}${game.earnings}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const CreateLeagueModal = ({ onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    name: '',
    buy_in: 50,
    max_players: 18,
    game_format: 'tournament',
    description: ''
  });
  const [loading, setLoading] = useState(false);
  const { token } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/api/leagues`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        onSuccess();
        onClose();
      } else {
        const error = await response.json();
        alert(error.detail);
      }
    } catch (error) {
      console.error('Error creating league:', error);
    }
    setLoading(false);
  };

  return (
    <div className="modal-overlay">
      <div className="modal">
        <div className="modal-header">
          <h2>Create New League</h2>
          <button onClick={onClose} className="close-button">✕</button>
        </div>
        
        <form onSubmit={handleSubmit} className="create-form">
          <div className="form-group">
            <label>League Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              required
              placeholder="Friday Night Poker"
            />
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label>Buy-in ($)</label>
              <input
                type="number"
                value={formData.buy_in}
                onChange={(e) => setFormData({...formData, buy_in: parseInt(e.target.value)})}
                min="1"
                required
              />
            </div>
            
            <div className="form-group">
              <label>Max Players</label>
              <input
                type="number"
                value={formData.max_players}
                onChange={(e) => setFormData({...formData, max_players: parseInt(e.target.value)})}
                min="2"
                max="27"
                required
              />
            </div>
          </div>
          
          <div className="form-group">
            <label>Game Format</label>
            <select
              value={formData.game_format}
              onChange={(e) => setFormData({...formData, game_format: e.target.value})}
            >
              <option value="tournament">Tournament</option>
              <option value="cash">Cash Game</option>
            </select>
          </div>
          
          <div className="form-group">
            <label>Description (Optional)</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Weekly tournament with fun group of players"
              rows="3"
            />
          </div>
          
          <div className="form-actions">
            <button type="button" onClick={onClose} className="cancel-button">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="submit-button">
              {loading ? 'Creating...' : 'Create League'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Game Interface with Real-time Score Logging
const GameInterface = ({ league, onBack }) => {
  const [gameStatus, setGameStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [checkedInUsers, setCheckedInUsers] = useState(new Set());
  const [showScoreModal, setShowScoreModal] = useState(false);
  const [showResultsForm, setShowResultsForm] = useState(false);
  const { user, token } = useAuth();

  useEffect(() => {
    fetchGameStatus();
    const interval = setInterval(fetchGameStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const fetchGameStatus = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/game/${league.id}/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setGameStatus(data);
        setCheckedInUsers(new Set(data.seat_assignments.map(a => a.user_id)));
        setLoading(false);
      }
    } catch (error) {
      console.error('Error fetching game status:', error);
      setLoading(false);
    }
  };

  const handleCheckIn = async (action) => {
    if (action === 'check_out' && gameStatus?.game_started && checkedInUsers.has(user.id)) {
      // Show score modal for elimination during active game
      setShowScoreModal(true);
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/game/${league.id}/checkin`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          league_id: league.id,
          action: action
        }),
      });

      if (response.ok) {
        fetchGameStatus();
      }
    } catch (error) {
      console.error('Error checking in/out:', error);
    }
  };

  const startGame = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/game/${league.id}/start`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        fetchGameStatus();
      }
    } catch (error) {
      console.error('Error starting game:', error);
    }
  };

  const resetGame = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/game/${league.id}/reset`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        fetchGameStatus();
      }
    } catch (error) {
      console.error('Error resetting game:', error);
    }
  };

  const renderPokerTable = (tableNumber, assignments) => {
    const tableSeats = assignments.filter(a => a.table_number === tableNumber);
    
    return (
      <div key={tableNumber} className="poker-table">
        <div className="table-header">
          <h3>Table {tableNumber}</h3>
          <span className="player-count">{tableSeats.length}/9 Players</span>
        </div>
        <div className="table-surface">
          <div className="table-center">
            <div className="table-number">{tableNumber}</div>
            <div className="table-label">POKER</div>
          </div>
          <div className="seats-container">
            {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(seatNum => {
              const player = tableSeats.find(s => s.seat_number === seatNum);
              return (
                <div 
                  key={seatNum} 
                  className={`seat seat-${seatNum} ${player ? 'occupied' : 'empty'}`}
                >
                  {player ? (
                    <div className="player-seat">
                      <div className="player-avatar">{player.user_avatar}</div>
                      <div className="player-name">{player.user_name}</div>
                      <div className="seat-number">Seat {seatNum}</div>
                    </div>
                  ) : (
                    <div className="empty-seat">
                      <div className="seat-number">{seatNum}</div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="game-loading">
        <div className="loading-spinner"></div>
        <p>Loading game room...</p>
      </div>
    );
  }

  const tables = gameStatus?.seat_assignments ? 
    [...new Set(gameStatus.seat_assignments.map(a => a.table_number))] : [];
  
  const isCheckedIn = checkedInUsers.has(user.id);
  const isAdmin = league.admin_id === user.id;
  const isEliminated = gameStatus?.live_eliminations?.some(e => e.user_id === user.id);

  return (
    <div className="game-interface">
      <header className="game-header">
        <button onClick={onBack} className="back-button">← Back to Dashboard</button>
        <h1>♠️ {gameStatus?.league_name || league.name} ♠️</h1>
        <div className="game-stats">
          <div className="stat">
            <span className="stat-value">{gameStatus?.checked_in_players || 0}</span>
            <span className="stat-label">Active</span>
          </div>
          <div className="stat">
            <span className="stat-value">{gameStatus?.eliminated_count || 0}</span>
            <span className="stat-label">Eliminated</span>
          </div>
          <div className="stat">
            <span className="stat-value">{gameStatus?.tables_needed || 0}</span>
            <span className="stat-label">Tables</span>
          </div>
        </div>
      </header>

      <div className="game-content">
        <div className="game-sidebar">
          <div className="check-in-section">
            <h2>Game Status</h2>
            
            <div className="my-checkin">
              <div className={`my-status ${isCheckedIn ? 'checked-in' : ''} ${isEliminated ? 'eliminated' : ''}`}>
                <span className="my-avatar">{user.avatar}</span>
                <span className="my-name">{user.name}</span>
                {isEliminated ? (
                  <span className="eliminated-badge">💀 Eliminated</span>
                ) : (
                  <button
                    className={`my-checkin-btn ${isCheckedIn ? 'checked-in' : ''} ${gameStatus?.game_started && isCheckedIn ? 'elimination-btn' : ''}`}
                    onClick={() => handleCheckIn(isCheckedIn ? 'check_out' : 'check_in')}
                    disabled={false}
                  >
                    {!isCheckedIn ? 'Check In' :
                     !gameStatus?.game_started ? '✓ Checked In' :
                     '💀 Get Eliminated'
                    }
                  </button>
                )}
              </div>
            </div>

            <div className="members-list">
              <h3>Active Players</h3>
              {gameStatus?.league_members?.map(member => {
                const memberCheckedIn = checkedInUsers.has(member.id);
                const memberEliminated = gameStatus?.live_eliminations?.some(e => e.user_id === member.id);
                
                if (memberEliminated) return null; // Don't show eliminated players in active list
                
                return (
                  <div key={member.id} className={`member-item ${memberCheckedIn ? 'checked-in' : ''}`}>
                    <span className="member-avatar">{member.avatar}</span>
                    <span className="member-name">{member.name}</span>
                    {memberCheckedIn && <span className="check-mark">✓</span>}
                  </div>
                );
              })}
            </div>

            {gameStatus?.live_eliminations && gameStatus.live_eliminations.length > 0 && (
              <div className="eliminations-list">
                <h3>Eliminations</h3>
                {gameStatus.live_eliminations
                  .sort((a, b) => a.finish_position - b.finish_position)
                  .map(elimination => (
                  <div key={elimination.user_id} className="elimination-item">
                    <div className="elimination-info">
                      <span className="elimination-avatar">{elimination.user_avatar}</span>
                      <span className="elimination-name">{elimination.user_name}</span>
                    </div>
                    <div className="elimination-result">
                      <span className={`finish-pos ${elimination.finish_position <= 3 ? 'top-three' : ''}`}>
                        {elimination.finish_position === 1 ? '🥇' : 
                         elimination.finish_position === 2 ? '🥈' : 
                         elimination.finish_position === 3 ? '🥉' : 
                         `#${elimination.finish_position}`}
                      </span>
                      <span className="points">+{elimination.points_earned} pts</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {isAdmin && (
            <div className="admin-controls">
              <h3>Admin Controls</h3>
              <button 
                className="start-game-btn"
                onClick={startGame}
                disabled={!gameStatus || gameStatus.checked_in_players < 2 || gameStatus.game_started}
              >
                {gameStatus?.game_started ? '🎮 Game Started' : '🚀 Start Game'}
              </button>
              
              {gameStatus?.game_started && !gameStatus?.game_completed && (
                <button 
                  className="complete-game-btn"
                  onClick={() => setShowResultsForm(true)}
                >
                  🏁 Complete Game
                </button>
              )}
              
              <button 
                className="reset-game-btn"
                onClick={resetGame}
              >
                🔄 Reset Game
              </button>
            </div>
          )}
        </div>

        <div className="tables-area">
          <div className="tables-header">
            <h2>🎯 Live Tournament</h2>
            {gameStatus?.game_started && (
              <p className="tournament-info">
                {gameStatus.total_initial_players} players started • {gameStatus.checked_in_players} remaining
              </p>
            )}
          </div>

          {gameStatus?.checked_in_players === 0 ? (
            <div className="no-players">
              <div className="empty-state">
                <div className="empty-icon">🃏</div>
                <h3>No Active Players</h3>
                <p>Players will be automatically assigned seats as they check in</p>
              </div>
            </div>
          ) : (
            <div className="tables-grid">
              {tables.map(tableNum => 
                renderPokerTable(tableNum, gameStatus.seat_assignments)
              )}
            </div>
          )}
        </div>
      </div>

      {showScoreModal && (
        <ScoreLogModal 
          gameStatus={gameStatus}
          league={league}
          onClose={() => setShowScoreModal(false)}
          onSuccess={() => {
            setShowScoreModal(false);
            fetchGameStatus();
          }}
        />
      )}

      {showResultsForm && (
        <GameResultsModal 
          gameStatus={gameStatus}
          league={league}
          onClose={() => setShowResultsForm(false)}
          onSuccess={() => {
            setShowResultsForm(false);
            fetchGameStatus();
          }}
        />
      )}
    </div>
  );
};

const ScoreLogModal = ({ gameStatus, league, onClose, onSuccess }) => {
  const [finishPosition, setFinishPosition] = useState('');
  const [loading, setLoading] = useState(false);
  const { token } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/api/game/${league.id}/checkin`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          league_id: league.id,
          action: 'check_out',
          finish_position: parseInt(finishPosition)
        })
      });

      if (response.ok) {
        const result = await response.json();
        onSuccess();
        // Show success message
        if (result.points_earned) {
          alert(`Eliminated in position #${finishPosition}! You earned ${result.points_earned} points and ${result.earnings >= 0 ? 'won' : 'lost'} $${Math.abs(result.earnings)}.`);
        }
      } else {
        const error = await response.json();
        alert(error.detail);
      }
    } catch (error) {
      console.error('Error logging score:', error);
      alert('Error logging your score. Please try again.');
    }
    setLoading(false);
  };

  const maxPosition = gameStatus?.total_initial_players || 1;
  const eliminatedPositions = new Set(gameStatus?.live_eliminations?.map(e => e.finish_position) || []);

  return (
    <div className="modal-overlay">
      <div className="modal">
        <div className="modal-header">
          <h2>🎯 Log Your Score</h2>
          <button onClick={onClose} className="close-button">✕</button>
        </div>
        
        <div className="score-info">
          <p>You've been eliminated from the tournament!</p>
          <p>Please select your final position:</p>
        </div>
        
        <form onSubmit={handleSubmit} className="score-form">
          <div className="form-group">
            <label>Finish Position</label>
            <select
              value={finishPosition}
              onChange={(e) => setFinishPosition(e.target.value)}
              required
              className="position-select"
            >
              <option value="">Select your position...</option>
              {Array.from({length: maxPosition}, (_, i) => i + 1)
                .filter(pos => !eliminatedPositions.has(pos))
                .map(pos => (
                <option key={pos} value={pos}>
                  {pos === 1 ? '🥇 1st Place' : 
                   pos === 2 ? '🥈 2nd Place' : 
                   pos === 3 ? '🥉 3rd Place' : 
                   `#${pos}`}
                </option>
              ))}
            </select>
          </div>
          
          <div className="form-actions">
            <button type="button" onClick={onClose} className="cancel-button">
              Cancel
            </button>
            <button type="submit" disabled={loading || !finishPosition} className="submit-button">
              {loading ? 'Submitting...' : 'Log Score'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const GameResultsModal = ({ gameStatus, league, onClose, onSuccess }) => {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const { token } = useAuth();

  useEffect(() => {
    // Initialize results with all initial players
    const initialResults = gameStatus.league_members.map((member, index) => ({
      user_id: member.id,
      user_name: member.name,
      finish_position: index + 1,
      points_earned: 0,
      buy_in_paid: league.buy_in
    }));
    setResults(initialResults);
  }, [gameStatus, league]);

  const handlePositionChange = (userIndex, newPosition) => {
    const newResults = [...results];
    const oldPosition = newResults[userIndex].finish_position;
    
    // Update the current player's position
    newResults[userIndex].finish_position = newPosition;
    
    // Adjust other players' positions
    newResults.forEach((result, index) => {
      if (index !== userIndex) {
        if (newPosition <= oldPosition) {
          // Moving up - push others down
          if (result.finish_position >= newPosition && result.finish_position < oldPosition) {
            result.finish_position += 1;
          }
        } else {
          // Moving down - pull others up
          if (result.finish_position > oldPosition && result.finish_position <= newPosition) {
            result.finish_position -= 1;
          }
        }
      }
    });
    
    // Sort by position and update points
    newResults.sort((a, b) => a.finish_position - b.finish_position);
    setResults(newResults);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/api/game/${league.id}/complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ results })
      });

      if (response.ok) {
        onSuccess();
      } else {
        const error = await response.json();
        alert(error.detail);
      }
    } catch (error) {
      console.error('Error submitting results:', error);
    }
    setLoading(false);
  };

  return (
    <div className="modal-overlay">
      <div className="modal large-modal">
        <div className="modal-header">
          <h2>🏁 Final Game Results</h2>
          <button onClick={onClose} className="close-button">✕</button>
        </div>
        
        <form onSubmit={handleSubmit} className="results-form">
          <p>Set the final positions for all players (this will override live eliminations):</p>
          
          <div className="results-list">
            {results.map((result, index) => (
              <div key={result.user_id} className="result-item">
                <div className="player-info">
                  <span className="player-name">{result.user_name}</span>
                </div>
                <div className="position-selector">
                  <label>Finish Position:</label>
                  <select
                    value={result.finish_position}
                    onChange={(e) => handlePositionChange(index, parseInt(e.target.value))}
                  >
                    {Array.from({length: results.length}, (_, i) => i + 1).map(pos => (
                      <option key={pos} value={pos}>
                        {pos === 1 ? '🥇 1st' : pos === 2 ? '🥈 2nd' : pos === 3 ? '🥉 3rd' : `${pos}th`}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            ))}
          </div>
          
          <div className="form-actions">
            <button type="button" onClick={onClose} className="cancel-button">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="submit-button">
              {loading ? 'Submitting...' : 'Complete Game'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="app">
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Loading Poker League...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      {user ? <Dashboard /> : <AuthForm />}
    </div>
  );
}

function AppWithAuth() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}

export default AppWithAuth;