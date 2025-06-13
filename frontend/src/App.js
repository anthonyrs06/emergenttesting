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
      </div>

      <div className="dashboard-content">
        {loading ? (
          <div className="loading">
            <div className="loading-spinner"></div>
            <p>Loading leagues...</p>
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

// Game Interface (updated to work with real users)
const GameInterface = ({ league, onBack }) => {
  const [gameStatus, setGameStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [checkedInUsers, setCheckedInUsers] = useState(new Set());
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

  return (
    <div className="game-interface">
      <header className="game-header">
        <button onClick={onBack} className="back-button">← Back to Dashboard</button>
        <h1>♠️ {gameStatus?.league_name || league.name} ♠️</h1>
        <div className="game-stats">
          <div className="stat">
            <span className="stat-value">{gameStatus?.checked_in_players || 0}</span>
            <span className="stat-label">Checked In</span>
          </div>
          <div className="stat">
            <span className="stat-value">{gameStatus?.tables_needed || 0}</span>
            <span className="stat-label">Tables</span>
          </div>
          <div className="stat">
            <span className="stat-value">{gameStatus?.total_members || 0}</span>
            <span className="stat-label">Members</span>
          </div>
        </div>
      </header>

      <div className="game-content">
        <div className="game-sidebar">
          <div className="check-in-section">
            <h2>Game Day Check-In</h2>
            
            <div className="my-checkin">
              <div className={`my-status ${isCheckedIn ? 'checked-in' : ''}`}>
                <span className="my-avatar">{user.avatar}</span>
                <span className="my-name">{user.name}</span>
                <button
                  className={`my-checkin-btn ${isCheckedIn ? 'checked-in' : ''}`}
                  onClick={() => handleCheckIn(isCheckedIn ? 'check_out' : 'check_in')}
                >
                  {isCheckedIn ? '✓ Checked In' : 'Check In'}
                </button>
              </div>
            </div>

            <div className="members-list">
              <h3>League Members</h3>
              {gameStatus?.league_members?.map(member => {
                const memberCheckedIn = checkedInUsers.has(member.id);
                return (
                  <div key={member.id} className={`member-item ${memberCheckedIn ? 'checked-in' : ''}`}>
                    <span className="member-avatar">{member.avatar}</span>
                    <span className="member-name">{member.name}</span>
                    {memberCheckedIn && <span className="check-mark">✓</span>}
                  </div>
                );
              })}
            </div>
          </div>

          {isAdmin && (
            <div className="admin-controls">
              <h3>Admin Controls</h3>
              <button 
                className="start-game-btn"
                onClick={startGame}
                disabled={!gameStatus || gameStatus.checked_in_players < 2}
              >
                {gameStatus?.game_started ? '🎮 Game Started' : '🚀 Start Game'}
              </button>
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
            <h2>🎯 Seat Assignments</h2>
            {gameStatus?.checked_in_players > 0 && (
              <p className="assignment-info">
                Auto-assigned {gameStatus.checked_in_players} players across {gameStatus.tables_needed} table{gameStatus.tables_needed > 1 ? 's' : ''}
              </p>
            )}
          </div>

          {gameStatus?.checked_in_players === 0 ? (
            <div className="no-players">
              <div className="empty-state">
                <div className="empty-icon">🃏</div>
                <h3>No Players Checked In</h3>
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