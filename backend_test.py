import requests
import unittest
import sys
import os
import uuid
import random
from datetime import datetime

class PokerLeagueAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.token = None
        self.user = None
        self.test_users = []
        self.test_league = None

    def run_test(self, name, method, endpoint, expected_status, data=None, auth=False):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Response text: {response.text}")
                return success, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    # Authentication Tests
    def test_register_user(self, email=None, password="Test123!", name=None):
        """Test user registration"""
        if not email:
            email = f"test{uuid.uuid4().hex[:8]}@example.com"
        if not name:
            name = f"Test User {uuid.uuid4().hex[:5]}"
            
        data = {
            "email": email,
            "password": password,
            "name": name
        }
        
        success, response = self.run_test(
            "Register User",
            "POST",
            "api/auth/register",
            200,
            data=data
        )
        
        if success:
            print(f"Registered user: {response.get('user', {}).get('name')}")
            self.token = response.get('access_token')
            self.user = response.get('user')
            return success, self.user
        return success, None

    def test_login_user(self, email, password="Test123!"):
        """Test user login"""
        data = {
            "email": email,
            "password": password
        }
        
        success, response = self.run_test(
            "Login User",
            "POST",
            "api/auth/login",
            200,
            data=data
        )
        
        if success:
            print(f"Logged in user: {response.get('user', {}).get('name')}")
            self.token = response.get('access_token')
            self.user = response.get('user')
            return success, self.user
        return success, None

    def test_get_current_user(self):
        """Test getting current user info"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "api/auth/me",
            200,
            auth=True
        )
        
        if success:
            print(f"Current user: {response.get('name')}")
        return success, response

    # League Tests
    def test_create_league(self, name=None, buy_in=50, max_players=18):
        """Test creating a league"""
        if not name:
            name = f"Test League {uuid.uuid4().hex[:5]}"
            
        data = {
            "name": name,
            "buy_in": buy_in,
            "max_players": max_players,
            "game_format": "tournament",
            "description": "Test league for API testing"
        }
        
        success, response = self.run_test(
            "Create League",
            "POST",
            "api/leagues",
            200,
            data=data,
            auth=True
        )
        
        if success:
            print(f"Created league: {name} with ID: {response.get('league_id')}")
            return success, response.get('league_id')
        return success, None

    def test_get_leagues(self):
        """Test getting all leagues"""
        success, response = self.run_test(
            "Get All Leagues",
            "GET",
            "api/leagues",
            200,
            auth=True
        )
        
        if success:
            print(f"Retrieved {len(response)} leagues")
        return success, response

    def test_get_my_leagues(self):
        """Test getting user's leagues"""
        success, response = self.run_test(
            "Get My Leagues",
            "GET",
            "api/leagues/my",
            200,
            auth=True
        )
        
        if success:
            print(f"Retrieved {len(response)} of my leagues")
        return success, response

    def test_join_league(self, league_id):
        """Test joining a league"""
        data = {
            "league_id": league_id
        }
        
        success, response = self.run_test(
            "Join League",
            "POST",
            "api/leagues/join",
            200,
            data=data,
            auth=True
        )
        
        if success:
            print(f"Joined league: {response.get('message')}")
        return success, response

    # Game Tests
    def test_get_game_status(self, league_id):
        """Test getting game status for a league"""
        success, response = self.run_test(
            "Get Game Status",
            "GET",
            f"api/game/{league_id}/status",
            200,
            auth=True
        )
        
        if success:
            print(f"Game status: {response.get('checked_in_players', 0)} players checked in")
            print(f"Tables needed: {response.get('tables_needed', 0)}")
        return success, response

    def test_player_checkin(self, league_id, action="check_in"):
        """Test checking in a player"""
        data = {
            "league_id": league_id,
            "action": action
        }
        
        success, response = self.run_test(
            f"Player {action}",
            "POST",
            f"api/game/{league_id}/checkin",
            200,
            data=data,
            auth=True
        )
        
        if success:
            print(f"Player {action}: {response.get('message', '')}")
            print(f"Total checked in: {response.get('checked_in_count', 0)}")
        return success, response

    def test_start_game(self, league_id):
        """Test starting a game"""
        success, response = self.run_test(
            "Start Game",
            "POST",
            f"api/game/{league_id}/start",
            200,
            auth=True
        )
        
        if success:
            print(f"Game started: {response.get('message', '')}")
        return success, response

    def test_complete_game(self, league_id, results):
        """Test completing a game with results"""
        data = {
            "results": results
        }
        
        success, response = self.run_test(
            "Complete Game",
            "POST",
            f"api/game/{league_id}/complete",
            200,
            data=data,
            auth=True
        )
        
        if success:
            print(f"Game completed: {response.get('message', '')}")
            print(f"Total players: {response.get('total_players', 0)}")
            print(f"Prize pool: ${response.get('prize_pool', 0)}")
        return success, response

    def test_reset_game(self, league_id):
        """Test resetting a game"""
        success, response = self.run_test(
            "Reset Game",
            "POST",
            f"api/game/{league_id}/reset",
            200,
            auth=True
        )
        
        if success:
            print(f"Game reset: {response.get('message', '')}")
        return success, response

    # Leaderboard Tests
    def test_get_overall_leaderboard(self):
        """Test getting the overall leaderboard"""
        success, response = self.run_test(
            "Get Overall Leaderboard",
            "GET",
            "api/leaderboard",
            200,
            auth=True
        )
        
        if success:
            print(f"Retrieved leaderboard with {len(response)} entries")
            if len(response) > 0:
                top_player = response[0]
                print(f"Top player: {top_player.get('user_name')} with {top_player.get('total_points')} points")
        return success, response

    def test_get_league_leaderboard(self, league_id):
        """Test getting a league-specific leaderboard"""
        success, response = self.run_test(
            "Get League Leaderboard",
            "GET",
            f"api/leaderboard/league/{league_id}",
            200,
            auth=True
        )
        
        if success:
            print(f"Retrieved league leaderboard with {len(response)} entries")
        return success, response

    def test_get_user_stats(self, user_id):
        """Test getting user statistics"""
        success, response = self.run_test(
            "Get User Stats",
            "GET",
            f"api/stats/user/{user_id}",
            200,
            auth=True
        )
        
        if success:
            stats = response.get('stats', {})
            print(f"User stats: {stats.get('total_games', 0)} games played")
            print(f"Total points: {stats.get('total_points', 0)}")
            print(f"Win rate: {stats.get('win_rate', 0)}%")
            print(f"Total earnings: ${stats.get('total_earnings', 0)}")
        return success, response

    # Complete Flow Test
    def test_complete_tournament_flow(self):
        """Test the complete tournament flow from registration to leaderboard"""
        print("\n=== TESTING COMPLETE TOURNAMENT FLOW ===")
        
        # 1. Register admin user
        admin_success, admin = self.test_register_user()
        if not admin_success:
            print("❌ Failed to register admin user")
            return False
        
        admin_id = admin.get('id')
        admin_email = admin.get('email')
        
        # 2. Create a league
        league_success, league_id = self.test_create_league(buy_in=100)
        if not league_success or not league_id:
            print("❌ Failed to create league")
            return False
        
        self.test_league = league_id
        
        # 3. Register 5 more test users
        test_users = []
        for i in range(5):
            # Save admin token
            admin_token = self.token
            
            # Register new user
            user_success, user = self.test_register_user()
            if user_success and user:
                test_users.append(user)
                
                # Join the league with this user
                join_success, _ = self.test_join_league(league_id)
                if not join_success:
                    print(f"❌ Failed to join league for user {user.get('name')}")
            
            # Restore admin token
            self.token = admin_token
            self.user = admin
        
        self.test_users = test_users
        
        if len(test_users) < 3:
            print("❌ Failed to create enough test users")
            return False
        
        print(f"✅ Created {len(test_users)} test users who joined the league")
        
        # 4. Check-in all users (admin + test users)
        for user in [admin] + test_users:
            # Login as this user
            login_success, _ = self.test_login_user(user.get('email'))
            if login_success:
                # Check in
                checkin_success, _ = self.test_player_checkin(league_id)
                if not checkin_success:
                    print(f"❌ Failed to check in user {user.get('name')}")
        
        # 5. Login as admin and start the game
        login_success, _ = self.test_login_user(admin_email)
        if not login_success:
            print("❌ Failed to log back in as admin")
            return False
        
        # Get game status to verify check-ins
        _, game_status = self.test_get_game_status(league_id)
        checked_in = game_status.get('checked_in_players', 0)
        print(f"✅ {checked_in} players checked in")
        
        # Start the game
        start_success, _ = self.test_start_game(league_id)
        if not start_success:
            print("❌ Failed to start the game")
            return False
        
        print("✅ Game started successfully")
        
        # 6. Complete the game with results
        all_players = [admin] + test_users
        # Shuffle players to randomize finish positions
        random.shuffle(all_players)
        
        results = []
        for i, player in enumerate(all_players):
            results.append({
                "user_id": player.get('id'),
                "user_name": player.get('name'),
                "finish_position": i + 1,
                "points_earned": 0,  # Will be calculated by backend
                "buy_in_paid": 100
            })
        
        complete_success, _ = self.test_complete_game(league_id, results)
        if not complete_success:
            print("❌ Failed to complete the game")
            return False
        
        print("✅ Game completed successfully with results")
        
        # 7. Check leaderboard
        leaderboard_success, leaderboard = self.test_get_league_leaderboard(league_id)
        if not leaderboard_success:
            print("❌ Failed to get league leaderboard")
            return False
        
        if len(leaderboard) != len(all_players):
            print(f"❌ Expected {len(all_players)} players on leaderboard, got {len(leaderboard)}")
        else:
            print(f"✅ Leaderboard has correct number of players: {len(leaderboard)}")
        
        # 8. Check overall leaderboard
        overall_success, _ = self.test_get_overall_leaderboard()
        if not overall_success:
            print("❌ Failed to get overall leaderboard")
            return False
        
        # 9. Check user stats for winner
        winner_id = results[0]["user_id"]
        stats_success, stats = self.test_get_user_stats(winner_id)
        if not stats_success:
            print("❌ Failed to get user stats")
            return False
        
        # Verify winner has correct stats
        user_stats = stats.get('stats', {})
        if user_stats.get('total_games', 0) != 1:
            print(f"❌ Expected winner to have 1 game, got {user_stats.get('total_games', 0)}")
        else:
            print("✅ Winner has correct game count")
        
        if user_stats.get('total_wins', 0) != 1:
            print(f"❌ Expected winner to have 1 win, got {user_stats.get('total_wins', 0)}")
        else:
            print("✅ Winner has correct win count")
        
        if user_stats.get('win_rate', 0) != 100.0:
            print(f"❌ Expected winner to have 100% win rate, got {user_stats.get('win_rate', 0)}%")
        else:
            print("✅ Winner has correct win rate")
        
        # 10. Reset the game
        reset_success, _ = self.test_reset_game(league_id)
        if not reset_success:
            print("❌ Failed to reset the game")
            return False
        
        print("✅ Game reset successfully")
        print("✅ Complete tournament flow test passed!")
        return True

def main():
    # Get backend URL from frontend .env
    backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'https://a9a27050-24da-4065-a659-67dc159b3097.preview.emergentagent.com')
    
    print(f"Testing against backend URL: {backend_url}")
    
    # Setup
    tester = PokerLeagueAPITester(backend_url)
    
    # Run tests
    print("\n=== POKER LEAGUE API TESTS ===")
    
    # Test complete tournament flow
    tester.test_complete_tournament_flow()
    
    # Test individual endpoints
    print("\n=== TESTING INDIVIDUAL ENDPOINTS ===")
    
    # If we have a test user and league from the flow test, use them
    if tester.user and tester.test_league:
        # Test leaderboard endpoints
        tester.test_get_overall_leaderboard()
        tester.test_get_league_leaderboard(tester.test_league)
        
        # Test user stats
        tester.test_get_user_stats(tester.user.get('id'))
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())