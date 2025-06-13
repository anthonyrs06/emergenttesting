import React, { useState, useEffect } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [players, setPlayers] = useState([]);
  const [gameStatus, setGameStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [checkedInPlayers, setCheckedInPlayers] = useState(new Set());

  useEffect(() => {
    fetchPlayers();
    fetchGameStatus();
    // Poll for updates every 2 seconds
    const interval = setInterval(fetchGameStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const fetchPlayers = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/players`);
      const data = await response.json();
      setPlayers(data);
    } catch (error) {
      console.error('Error fetching players:', error);
    }
  };

  const fetchGameStatus = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/game/status`);
      const data = await response.json();
      setGameStatus(data);
      setCheckedInPlayers(new Set(data.seat_assignments.map(a => a.player_id)));
      setLoading(false);
    } catch (error) {
      console.error('Error fetching game status:', error);
      setLoading(false);
    }
  };

  const handleCheckIn = async (playerId, isCheckedIn) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/game/checkin`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          player_id: playerId,
          action: isCheckedIn ? 'check_out' : 'check_in'
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
      const response = await fetch(`${BACKEND_URL}/api/game/start`, {
        method: 'POST',
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
      const response = await fetch(`${BACKEND_URL}/api/game/reset`, {
        method: 'POST',
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
                      <div className="player-avatar">{player.player_avatar}</div>
                      <div className="player-name">{player.player_name}</div>
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
      <div className="app">
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Loading Poker League...</p>
        </div>
      </div>
    );
  }

  const tables = gameStatus?.seat_assignments ? 
    [...new Set(gameStatus.seat_assignments.map(a => a.table_number))] : [];

  return (
    <div className="app">
      <header className="app-header">
        <h1>♠️ {gameStatus?.league_name || 'Poker League'} ♠️</h1>
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
            <span className="stat-value">{gameStatus?.total_players || 0}</span>
            <span className="stat-label">Total Players</span>
          </div>
        </div>
      </header>

      <div className="main-content">
        <div className="sidebar">
          <div className="check-in-section">
            <h2>Game Day Check-In</h2>
            <div className="players-list">
              {players.map(player => {
                const isCheckedIn = checkedInPlayers.has(player.id);
                return (
                  <div key={player.id} className={`player-item ${isCheckedIn ? 'checked-in' : ''}`}>
                    <div className="player-info">
                      <span className="player-avatar">{player.avatar}</span>
                      <span className="player-name">{player.name}</span>
                    </div>
                    <button
                      className={`check-in-btn ${isCheckedIn ? 'checked-in' : ''}`}
                      onClick={() => handleCheckIn(player.id, isCheckedIn)}
                    >
                      {isCheckedIn ? '✓ Checked In' : 'Check In'}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="game-controls">
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
}

export default App;