from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid
from datetime import datetime
import os

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock Data
MOCK_LEAGUES = {
    "league1": {
        "id": "league1",
        "name": "Friday Night Poker",
        "buy_in": 50,
        "max_players": 27,
        "game_format": "tournament",
        "admin_id": "admin1"
    }
}

MOCK_PLAYERS = {
    "player1": {"id": "player1", "name": "Alex Chen", "avatar": "🎯"},
    "player2": {"id": "player2", "name": "Sarah Johnson", "avatar": "♠️"},
    "player3": {"id": "player3", "name": "Mike Rodriguez", "avatar": "♥️"},
    "player4": {"id": "player4", "name": "Emma Wilson", "avatar": "♣️"},
    "player5": {"id": "player5", "name": "David Kim", "avatar": "♦️"},
    "player6": {"id": "player6", "name": "Lisa Brown", "avatar": "🃏"},
    "player7": {"id": "player7", "name": "Tom Anderson", "avatar": "🎰"},
    "player8": {"id": "player8", "name": "Anna Martinez", "avatar": "🎲"},
    "player9": {"id": "player9", "name": "Chris Taylor", "avatar": "🎪"},
    "player10": {"id": "player10", "name": "Rachel Green", "avatar": "🎨"},
    "player11": {"id": "player11", "name": "Jason Lee", "avatar": "🎭"},
    "player12": {"id": "player12", "name": "Maria Garcia", "avatar": "🎸"},
    "player13": {"id": "player13", "name": "Kevin White", "avatar": "🎵"},
    "player14": {"id": "player14", "name": "Sophie Davis", "avatar": "🎺"},
    "player15": {"id": "player15", "name": "Ryan Miller", "avatar": "🎻"}
}

# Game state
game_state = {
    "league_id": "league1",
    "game_id": str(uuid.uuid4()),
    "checked_in_players": [],
    "seat_assignments": [],
    "game_started": False
}

# Models
class CheckInRequest(BaseModel):
    player_id: str
    action: str  # "check_in" or "check_out"

class SeatAssignment(BaseModel):
    table_number: int
    seat_number: int
    player_id: str
    player_name: str
    player_avatar: str

def calculate_seat_assignments(checked_in_players: List[str]) -> List[SeatAssignment]:
    """
    Algorithm to assign seats optimally across tables
    - Maximum 9 players per table
    - Distribute players evenly across tables
    - Return structured seat assignments
    """
    if not checked_in_players:
        return []
    
    num_players = len(checked_in_players)
    num_tables = (num_players + 8) // 9  # Ceiling division for max 9 per table
    
    # If we have more than 9 players, distribute evenly
    if num_tables > 1:
        players_per_table = num_players // num_tables
        extra_players = num_players % num_tables
    else:
        players_per_table = num_players
        extra_players = 0
    
    assignments = []
    player_index = 0
    
    for table in range(1, num_tables + 1):
        # Calculate how many players for this table
        table_size = players_per_table + (1 if table <= extra_players else 0)
        
        # Assign seats for this table
        for seat in range(1, table_size + 1):
            if player_index < len(checked_in_players):
                player_id = checked_in_players[player_index]
                player_data = MOCK_PLAYERS[player_id]
                
                assignments.append(SeatAssignment(
                    table_number=table,
                    seat_number=seat,
                    player_id=player_id,
                    player_name=player_data["name"],
                    player_avatar=player_data["avatar"]
                ))
                player_index += 1
    
    return assignments

@app.get("/api/league/{league_id}")
async def get_league(league_id: str):
    if league_id not in MOCK_LEAGUES:
        raise HTTPException(status_code=404, detail="League not found")
    return MOCK_LEAGUES[league_id]

@app.get("/api/players")
async def get_players():
    return list(MOCK_PLAYERS.values())

@app.get("/api/game/status")
async def get_game_status():
    # Calculate current seat assignments
    assignments = calculate_seat_assignments(game_state["checked_in_players"])
    game_state["seat_assignments"] = assignments
    
    return {
        "game_id": game_state["game_id"],
        "league_id": game_state["league_id"],
        "league_name": MOCK_LEAGUES[game_state["league_id"]]["name"],
        "checked_in_players": len(game_state["checked_in_players"]),
        "total_players": len(MOCK_PLAYERS),
        "seat_assignments": assignments,
        "game_started": game_state["game_started"],
        "tables_needed": max(1, (len(game_state["checked_in_players"]) + 8) // 9)
    }

@app.post("/api/game/checkin")
async def handle_checkin(request: CheckInRequest):
    player_id = request.player_id
    action = request.action
    
    if player_id not in MOCK_PLAYERS:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if action == "check_in":
        if player_id not in game_state["checked_in_players"]:
            game_state["checked_in_players"].append(player_id)
    elif action == "check_out":
        if player_id in game_state["checked_in_players"]:
            game_state["checked_in_players"].remove(player_id)
    
    # Recalculate seat assignments
    assignments = calculate_seat_assignments(game_state["checked_in_players"])
    game_state["seat_assignments"] = assignments
    
    return {
        "success": True,
        "message": f"Player {action.replace('_', ' ')}ed successfully",
        "checked_in_count": len(game_state["checked_in_players"]),
        "seat_assignments": assignments
    }

@app.post("/api/game/start")
async def start_game():
    if len(game_state["checked_in_players"]) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 players to start")
    
    game_state["game_started"] = True
    return {
        "success": True,
        "message": "Game started!",
        "game_id": game_state["game_id"]
    }

@app.post("/api/game/reset")
async def reset_game():
    game_state["checked_in_players"] = []
    game_state["seat_assignments"] = []
    game_state["game_started"] = False
    game_state["game_id"] = str(uuid.uuid4())
    
    return {
        "success": True,
        "message": "Game reset successfully"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)