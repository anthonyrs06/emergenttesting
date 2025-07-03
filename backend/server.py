from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional, Annotated
import uuid
from datetime import datetime, timedelta
import os
import jwt
import bcrypt
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'poker_league_db')

# JWT configuration
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# MongoDB client
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Security
security = HTTPBearer()

# Collections
users_collection = db.users
leagues_collection = db.leagues
memberships_collection = db.memberships
games_collection = db.games
game_results_collection = db.game_results

# Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime
    avatar: str = "🎯"

class LeagueCreate(BaseModel):
    name: str
    buy_in: int
    max_players: int
    game_format: str
    description: Optional[str] = ""

class League(BaseModel):
    id: str
    name: str
    buy_in: int
    max_players: int
    game_format: str
    description: str
    admin_id: str
    admin_name: str
    created_at: datetime
    member_count: int

class JoinLeagueRequest(BaseModel):
    league_id: str

class CheckInRequest(BaseModel):
    league_id: str
    action: str  # "check_in" or "check_out"

class GameResult(BaseModel):
    user_id: str
    user_name: str
    finish_position: int
    points_earned: int
    buy_in_paid: int

class GameResultSubmission(BaseModel):
    results: List[GameResult]

class SeatAssignment(BaseModel):
    table_number: int
    seat_number: int
    user_id: str
    user_name: str
    user_avatar: str

class LeaderboardEntry(BaseModel):
    user_id: str
    user_name: str
    user_avatar: str
    total_points: int
    games_played: int
    wins: int
    win_rate: float
    avg_finish: float
    total_earnings: int
    rank: int

# JWT helper functions
def create_access_token(user_id: str, email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expire
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

async def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> dict:
    token = credentials.credentials
    payload = verify_token(token)
    user = await users_collection.find_one({"id": payload["user_id"]})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def calculate_tournament_points(finish_position: int, total_players: int) -> int:
    """
    Calculate points based on finish position in tournament
    1st place gets 100 points, decreasing by position
    """
    if finish_position == 1:
        return 100
    elif finish_position == 2:
        return 80
    elif finish_position == 3:
        return 60
    elif finish_position <= 5:
        return 40
    elif finish_position <= 8:
        return 20
    else:
        return 10

def calculate_prize_distribution(total_players: int, buy_in: int) -> Dict[int, int]:
    """
    Calculate prize distribution based on number of players
    Simple structure: 1st=50%, 2nd=30%, 3rd=20% of prize pool
    """
    prize_pool = total_players * buy_in
    
    if total_players < 3:
        return {1: prize_pool}
    elif total_players < 6:
        return {
            1: int(prize_pool * 0.7),
            2: int(prize_pool * 0.3)
        }
    else:
        return {
            1: int(prize_pool * 0.5),
            2: int(prize_pool * 0.3),
            3: int(prize_pool * 0.2)
        }

def calculate_seat_assignments(checked_in_users: List[dict]) -> List[SeatAssignment]:
    """
    Algorithm to assign seats optimally across tables
    - Maximum 9 players per table
    - Distribute players evenly across tables
    - Return structured seat assignments
    """
    if not checked_in_users:
        return []
    
    num_players = len(checked_in_users)
    num_tables = (num_players + 8) // 9  # Ceiling division for max 9 per table
    
    # If we have more than 9 players, distribute evenly
    if num_tables > 1:
        players_per_table = num_players // num_tables
        extra_players = num_players % num_tables
    else:
        players_per_table = num_players
        extra_players = 0
    
    assignments = []
    user_index = 0
    
    for table in range(1, num_tables + 1):
        # Calculate how many players for this table
        table_size = players_per_table + (1 if table <= extra_players else 0)
        
        # Assign seats for this table
        for seat in range(1, table_size + 1):
            if user_index < len(checked_in_users):
                user = checked_in_users[user_index]
                
                assignments.append(SeatAssignment(
                    table_number=table,
                    seat_number=seat,
                    user_id=user["id"],
                    user_name=user["name"],
                    user_avatar=user["avatar"]
                ))
                user_index += 1
    
    return assignments

async def calculate_leaderboard(league_id: str = None) -> List[LeaderboardEntry]:
    """
    Calculate leaderboard for a specific league or overall
    """
    # Build query filter
    query_filter = {}
    if league_id:
        query_filter["league_id"] = league_id
    
    # Aggregate player statistics
    pipeline = [
        {"$match": query_filter},
        {
            "$group": {
                "_id": "$user_id",
                "user_name": {"$first": "$user_name"},
                "total_points": {"$sum": "$points_earned"},
                "games_played": {"$sum": 1},
                "wins": {
                    "$sum": {
                        "$cond": [{"$eq": ["$finish_position", 1]}, 1, 0]
                    }
                },
                "total_finish_positions": {"$sum": "$finish_position"},
                "total_earnings": {"$sum": "$earnings"}
            }
        },
        {
            "$project": {
                "_id": 1,
                "user_name": 1,
                "total_points": 1,
                "games_played": 1,
                "wins": 1,
                "win_rate": {
                    "$cond": [
                        {"$eq": ["$games_played", 0]},
                        0,
                        {"$divide": ["$wins", "$games_played"]}
                    ]
                },
                "avg_finish": {
                    "$cond": [
                        {"$eq": ["$games_played", 0]},
                        0,
                        {"$divide": ["$total_finish_positions", "$games_played"]}
                    ]
                },
                "total_earnings": 1
            }
        },
        {"$sort": {"total_points": -1}}
    ]
    
    leaderboard = []
    rank = 1
    
    async for result in game_results_collection.aggregate(pipeline):
        # Get user avatar
        user = await users_collection.find_one({"id": result["_id"]})
        user_avatar = user["avatar"] if user else "🎯"
        
        entry = LeaderboardEntry(
            user_id=result["_id"],
            user_name=result["user_name"],
            user_avatar=user_avatar,
            total_points=result["total_points"],
            games_played=result["games_played"],
            wins=result["wins"],
            win_rate=round(result["win_rate"] * 100, 1),
            avg_finish=round(result["avg_finish"], 1),
            total_earnings=result["total_earnings"],
            rank=rank
        )
        leaderboard.append(entry)
        rank += 1
    
    return leaderboard

# Auth endpoints
@app.post("/api/auth/register")
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = hash_password(user_data.password)
    
    avatars = ["🎯", "♠️", "♥️", "♣️", "♦️", "🃏", "🎰", "🎲", "🎪", "🎨", "🎭", "🎸", "🎵", "🎺", "🎻"]
    
    new_user = {
        "id": user_id,
        "email": user_data.email,
        "password": hashed_password,
        "name": user_data.name,
        "avatar": avatars[len(user_data.name) % len(avatars)],  # Simple avatar assignment
        "created_at": datetime.utcnow()
    }
    
    await users_collection.insert_one(new_user)
    
    # Create JWT token
    token = create_access_token(user_id, user_data.email)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": user_data.email,
            "name": user_data.name,
            "avatar": new_user["avatar"]
        }
    }

@app.post("/api/auth/login")
async def login(login_data: UserLogin):
    user = await users_collection.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    token = create_access_token(user["id"], user["email"])
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "avatar": user["avatar"]
        }
    }

@app.get("/api/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "name": current_user["name"],
        "avatar": current_user["avatar"]
    }

# League endpoints
@app.post("/api/leagues")
async def create_league(league_data: LeagueCreate, current_user: dict = Depends(get_current_user)):
    league_id = str(uuid.uuid4())
    
    new_league = {
        "id": league_id,
        "name": league_data.name,
        "buy_in": league_data.buy_in,
        "max_players": league_data.max_players,
        "game_format": league_data.game_format,
        "description": league_data.description,
        "admin_id": current_user["id"],
        "admin_name": current_user["name"],
        "created_at": datetime.utcnow()
    }
    
    await leagues_collection.insert_one(new_league)
    
    # Auto-join the creator as a member
    membership = {
        "id": str(uuid.uuid4()),
        "league_id": league_id,
        "user_id": current_user["id"],
        "user_name": current_user["name"],
        "user_avatar": current_user["avatar"],
        "status": "approved",
        "joined_at": datetime.utcnow()
    }
    await memberships_collection.insert_one(membership)
    
    return {"message": "League created successfully", "league_id": league_id}

@app.get("/api/leagues")
async def get_leagues(current_user: dict = Depends(get_current_user)):
    # Get all leagues with member counts
    leagues = []
    async for league in leagues_collection.find():
        # Count members for this league
        member_count = await memberships_collection.count_documents({
            "league_id": league["id"],
            "status": "approved"
        })
        
        league_data = {
            "id": league["id"],
            "name": league["name"],
            "buy_in": league["buy_in"],
            "max_players": league["max_players"],
            "game_format": league["game_format"],
            "description": league["description"],
            "admin_id": league["admin_id"],
            "admin_name": league["admin_name"],
            "created_at": league["created_at"],
            "member_count": member_count
        }
        leagues.append(league_data)
    
    return leagues

@app.get("/api/leagues/my")
async def get_my_leagues(current_user: dict = Depends(get_current_user)):
    # Get leagues where user is a member
    my_leagues = []
    async for membership in memberships_collection.find({
        "user_id": current_user["id"],
        "status": "approved"
    }):
        league = await leagues_collection.find_one({"id": membership["league_id"]})
        if league:
            member_count = await memberships_collection.count_documents({
                "league_id": league["id"],
                "status": "approved"
            })
            
            league_data = {
                "id": league["id"],
                "name": league["name"],
                "buy_in": league["buy_in"],
                "max_players": league["max_players"],
                "game_format": league["game_format"],
                "description": league["description"],
                "admin_id": league["admin_id"],
                "admin_name": league["admin_name"],
                "created_at": league["created_at"],
                "member_count": member_count,
                "is_admin": league["admin_id"] == current_user["id"]
            }
            my_leagues.append(league_data)
    
    return my_leagues

@app.post("/api/leagues/join")
async def join_league(request: JoinLeagueRequest, current_user: dict = Depends(get_current_user)):
    # Check if league exists
    league = await leagues_collection.find_one({"id": request.league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Check if already a member
    existing_membership = await memberships_collection.find_one({
        "league_id": request.league_id,
        "user_id": current_user["id"]
    })
    if existing_membership:
        raise HTTPException(status_code=400, detail="Already a member of this league")
    
    # Check if league is full
    member_count = await memberships_collection.count_documents({
        "league_id": request.league_id,
        "status": "approved"
    })
    if member_count >= league["max_players"]:
        raise HTTPException(status_code=400, detail="League is full")
    
    # Create membership
    membership = {
        "id": str(uuid.uuid4()),
        "league_id": request.league_id,
        "user_id": current_user["id"],
        "user_name": current_user["name"],
        "user_avatar": current_user["avatar"],
        "status": "approved",  # Auto-approve for MVP
        "joined_at": datetime.utcnow()
    }
    await memberships_collection.insert_one(membership)
    
    return {"message": "Successfully joined league"}

# Game endpoints
@app.get("/api/game/{league_id}/status")
async def get_game_status(league_id: str, current_user: dict = Depends(get_current_user)):
    # Check if user is member of this league
    membership = await memberships_collection.find_one({
        "league_id": league_id,
        "user_id": current_user["id"],
        "status": "approved"
    })
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this league")
    
    # Get league info
    league = await leagues_collection.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Get current game or create new one
    current_game = await games_collection.find_one({
        "league_id": league_id,
        "status": "active"
    })
    
    if not current_game:
        # Create new game
        game_id = str(uuid.uuid4())
        current_game = {
            "id": game_id,
            "league_id": league_id,
            "status": "active",
            "checked_in_users": [],
            "seat_assignments": [],
            "game_started": False,
            "created_at": datetime.utcnow()
        }
        await games_collection.insert_one(current_game)
    
    # Get all league members
    league_members = []
    async for membership in memberships_collection.find({
        "league_id": league_id,
        "status": "approved"
    }):
        league_members.append({
            "id": membership["user_id"],
            "name": membership["user_name"],
            "avatar": membership["user_avatar"]
        })
    
    # Calculate current seat assignments
    checked_in_users = [user for user in league_members if user["id"] in current_game["checked_in_users"]]
    assignments = calculate_seat_assignments(checked_in_users)
    
    return {
        "game_id": current_game["id"],
        "league_id": league_id,
        "league_name": league["name"],
        "league_members": league_members,
        "checked_in_players": len(current_game["checked_in_users"]),
        "total_members": len(league_members),
        "seat_assignments": assignments,
        "game_started": current_game["game_started"],
        "game_completed": current_game.get("game_completed", False),
        "tables_needed": max(1, (len(current_game["checked_in_users"]) + 8) // 9)
    }

@app.post("/api/game/{league_id}/checkin")
async def handle_checkin(league_id: str, request: CheckInRequest, current_user: dict = Depends(get_current_user)):
    # Check if user is member of this league
    membership = await memberships_collection.find_one({
        "league_id": league_id,
        "user_id": current_user["id"],
        "status": "approved"
    })
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this league")
    
    # Get current game
    current_game = await games_collection.find_one({
        "league_id": league_id,
        "status": "active"
    })
    if not current_game:
        raise HTTPException(status_code=404, detail="No active game found")
    
    # Update check-in status
    checked_in_users = current_game.get("checked_in_users", [])
    
    if request.action == "check_in":
        if current_user["id"] not in checked_in_users:
            checked_in_users.append(current_user["id"])
    elif request.action == "check_out":
        if current_user["id"] in checked_in_users:
            checked_in_users.remove(current_user["id"])
    
    # Update game in database
    await games_collection.update_one(
        {"id": current_game["id"]},
        {"$set": {"checked_in_users": checked_in_users}}
    )
    
    return {
        "success": True,
        "message": f"Successfully {request.action.replace('_', ' ')}ed",
        "checked_in_count": len(checked_in_users)
    }

@app.post("/api/game/{league_id}/start")
async def start_game(league_id: str, current_user: dict = Depends(get_current_user)):
    # Check if user is admin of this league
    league = await leagues_collection.find_one({"id": league_id})
    if not league or league["admin_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only league admin can start games")
    
    # Get current game
    current_game = await games_collection.find_one({
        "league_id": league_id,
        "status": "active"
    })
    if not current_game:
        raise HTTPException(status_code=404, detail="No active game found")
    
    if len(current_game.get("checked_in_users", [])) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 players to start")
    
    # Start game
    await games_collection.update_one(
        {"id": current_game["id"]},
        {"$set": {"game_started": True, "started_at": datetime.utcnow()}}
    )
    
    return {
        "success": True,
        "message": "Game started!",
        "game_id": current_game["id"]
    }

@app.post("/api/game/{league_id}/complete")
async def complete_game(league_id: str, submission: GameResultSubmission, current_user: dict = Depends(get_current_user)):
    # Check if user is admin of this league
    league = await leagues_collection.find_one({"id": league_id})
    if not league or league["admin_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only league admin can complete games")
    
    # Get current game
    current_game = await games_collection.find_one({
        "league_id": league_id,
        "status": "active"
    })
    if not current_game:
        raise HTTPException(status_code=404, detail="No active game found")
    
    if not current_game.get("game_started", False):
        raise HTTPException(status_code=400, detail="Game must be started before completing")
    
    # Calculate prize distribution
    total_players = len(submission.results)
    prize_distribution = calculate_prize_distribution(total_players, league["buy_in"])
    
    # Save game results
    for result in submission.results:
        # Calculate points and earnings
        points = calculate_tournament_points(result.finish_position, total_players)
        earnings = prize_distribution.get(result.finish_position, 0) - league["buy_in"]
        
        game_result = {
            "id": str(uuid.uuid4()),
            "game_id": current_game["id"],
            "league_id": league_id,
            "user_id": result.user_id,
            "user_name": result.user_name,
            "finish_position": result.finish_position,
            "points_earned": points,
            "buy_in_paid": league["buy_in"],
            "earnings": earnings,
            "created_at": datetime.utcnow()
        }
        await game_results_collection.insert_one(game_result)
    
    # Mark game as completed
    await games_collection.update_one(
        {"id": current_game["id"]},
        {"$set": {"game_completed": True, "completed_at": datetime.utcnow()}}
    )
    
    return {
        "success": True,
        "message": "Game completed and results saved!",
        "total_players": total_players,
        "prize_pool": total_players * league["buy_in"]
    }

@app.post("/api/game/{league_id}/reset")
async def reset_game(league_id: str, current_user: dict = Depends(get_current_user)):
    # Check if user is admin of this league
    league = await leagues_collection.find_one({"id": league_id})
    if not league or league["admin_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only league admin can reset games")
    
    # Create new game (end current one and start fresh)
    await games_collection.update_many(
        {"league_id": league_id, "status": "active"},
        {"$set": {"status": "completed"}}
    )
    
    # Create new active game
    game_id = str(uuid.uuid4())
    new_game = {
        "id": game_id,
        "league_id": league_id,
        "status": "active",
        "checked_in_users": [],
        "seat_assignments": [],
        "game_started": False,
        "created_at": datetime.utcnow()
    }
    await games_collection.insert_one(new_game)
    
    return {
        "success": True,
        "message": "Game reset successfully",
        "game_id": game_id
    }

# Leaderboard endpoints
@app.get("/api/leaderboard")
async def get_overall_leaderboard(current_user: dict = Depends(get_current_user)):
    """Get overall leaderboard across all leagues"""
    leaderboard = await calculate_leaderboard()
    return leaderboard

@app.get("/api/leaderboard/league/{league_id}")
async def get_league_leaderboard(league_id: str, current_user: dict = Depends(get_current_user)):
    """Get leaderboard for a specific league"""
    # Check if user is member of this league
    membership = await memberships_collection.find_one({
        "league_id": league_id,
        "user_id": current_user["id"],
        "status": "approved"
    })
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this league")
    
    leaderboard = await calculate_leaderboard(league_id)
    return leaderboard

@app.get("/api/stats/user/{user_id}")
async def get_user_stats(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get detailed stats for a specific user"""
    # Get user info
    user = await users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Calculate user statistics
    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": None,
                "total_points": {"$sum": "$points_earned"},
                "total_games": {"$sum": 1},
                "total_wins": {
                    "$sum": {"$cond": [{"$eq": ["$finish_position", 1]}, 1, 0]}
                },
                "total_earnings": {"$sum": "$earnings"},
                "avg_finish": {"$avg": "$finish_position"},
                "best_finish": {"$min": "$finish_position"}
            }
        }
    ]
    
    stats_result = await game_results_collection.aggregate(pipeline).to_list(1)
    
    if not stats_result:
        stats = {
            "total_points": 0,
            "total_games": 0,
            "total_wins": 0,
            "total_earnings": 0,
            "avg_finish": 0,
            "best_finish": 0,
            "win_rate": 0
        }
    else:
        stats = stats_result[0]
        stats["win_rate"] = (stats["total_wins"] / stats["total_games"]) * 100 if stats["total_games"] > 0 else 0
        stats["avg_finish"] = round(stats["avg_finish"], 1) if stats["avg_finish"] else 0
        stats["win_rate"] = round(stats["win_rate"], 1)
    
    # Get recent games
    recent_games = []
    async for result in game_results_collection.find({"user_id": user_id}).sort("created_at", -1).limit(10):
        # Get league info
        league = await leagues_collection.find_one({"id": result["league_id"]})
        recent_games.append({
            "game_id": result["game_id"],
            "league_name": league["name"] if league else "Unknown League",
            "finish_position": result["finish_position"],
            "points_earned": result["points_earned"],
            "earnings": result["earnings"],
            "created_at": result["created_at"]
        })
    
    return {
        "user": {
            "id": user["id"],
            "name": user["name"],
            "avatar": user["avatar"]
        },
        "stats": stats,
        "recent_games": recent_games
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)