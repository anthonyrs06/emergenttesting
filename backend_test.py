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

    def test_player_checkin(self, league_id, action="check_in", finish_position=None):
        """Test checking in a player or checking out with score"""
        data = {
            "league_id": league_id,
            "action": action
        }
        
        if finish_position is not None:
            data["finish_position"] = finish_position
        
        success, response = self.run_test(
            f"Player {action}" + (f" with position {finish_position}" if finish_position else ""),
            "POST",
            f"api/game/{league_id}/checkin",
            200,
            data=data,
            auth=True
        )
        
        if success:
            print(f"Player {action}: {response.get('message', '')}")
            print(f"Total checked in: {response.get('checked_in_count', 0)}")
            if finish_position and response.get('points_earned'):
                print(f"Points earned: {response.get('points_earned')}")
                print(f"Earnings: ${response.get('earnings')}")
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
    def test_real_time_score_logging_flow(self):
        """Test the NEW Real-Time Score Logging feature"""
        print("\n=== TESTING REAL-TIME SCORE LOGGING FLOW ===")
        
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
        
        # 3. Register 4 more test users (5 total players)
        test_users = []
        for i in range(4):
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
        
        if len(test_users) < 4:
            print("❌ Failed to create enough test users")
            return False
        
        print(f"✅ Created {len(test_users)} test users who joined the league")
        
        # 4. Get initial game status
        _, game_status = self.test_get_game_status(league_id)
        if not game_status:
            print("❌ Failed to get initial game status")
            return False
            
        print("✅ Game initialized successfully")
        
        # 5. Check-in all users (admin + test users)
        all_players = [admin] + test_users
        for user in all_players:
            # Login as this user
            login_success, _ = self.test_login_user(user.get('email'))
            if login_success:
                # Check in
                checkin_success, _ = self.test_player_checkin(league_id)
                if not checkin_success:
                    print(f"❌ Failed to check in user {user.get('name')}")
                else:
                    print(f"✅ Checked in user {user.get('name')}")
        
        # 6. Login as admin and start the game
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
        
        # 7. TEST REAL-TIME ELIMINATIONS - Players get eliminated one by one
        print("\n--- TESTING REAL-TIME ELIMINATIONS ---")
        
        # Player 1 gets eliminated in 5th place (last place)
        login_success, _ = self.test_login_user(test_users[0].get('email'))
        if login_success:
            elimination_success, elimination_response = self.test_player_checkin(
                league_id, action="check_out", finish_position=5
            )
            if elimination_success:
                print(f"✅ Player 1 eliminated in 5th place")
                print(f"   Points earned: {elimination_response.get('points_earned', 0)}")
                print(f"   Earnings: ${elimination_response.get('earnings', 0)}")
            else:
                print("❌ Failed to eliminate player 1")
                return False
        
        # Player 2 gets eliminated in 4th place
        login_success, _ = self.test_login_user(test_users[1].get('email'))
        if login_success:
            elimination_success, elimination_response = self.test_player_checkin(
                league_id, action="check_out", finish_position=4
            )
            if elimination_success:
                print(f"✅ Player 2 eliminated in 4th place")
                print(f"   Points earned: {elimination_response.get('points_earned', 0)}")
                print(f"   Earnings: ${elimination_response.get('earnings', 0)}")
            else:
                print("❌ Failed to eliminate player 2")
                return False
        
        # Player 3 gets eliminated in 3rd place
        login_success, _ = self.test_login_user(test_users[2].get('email'))
        if login_success:
            elimination_success, elimination_response = self.test_player_checkin(
                league_id, action="check_out", finish_position=3
            )
            if elimination_success:
                print(f"✅ Player 3 eliminated in 3rd place")
                print(f"   Points earned: {elimination_response.get('points_earned', 0)}")
                print(f"   Earnings: ${elimination_response.get('earnings', 0)}")
            else:
                print("❌ Failed to eliminate player 3")
                return False
        
        # Player 4 gets eliminated in 2nd place
        login_success, _ = self.test_login_user(test_users[3].get('email'))
        if login_success:
            elimination_success, elimination_response = self.test_player_checkin(
                league_id, action="check_out", finish_position=2
            )
            if elimination_success:
                print(f"✅ Player 4 eliminated in 2nd place")
                print(f"   Points earned: {elimination_response.get('points_earned', 0)}")
                print(f"   Earnings: ${elimination_response.get('earnings', 0)}")
            else:
                print("❌ Failed to eliminate player 4")
                return False
        
        # Admin wins (1st place) - eliminate themselves
        login_success, _ = self.test_login_user(admin_email)
        if login_success:
            elimination_success, elimination_response = self.test_player_checkin(
                league_id, action="check_out", finish_position=1
            )
            if elimination_success:
                print(f"✅ Admin wins in 1st place")
                print(f"   Points earned: {elimination_response.get('points_earned', 0)}")
                print(f"   Earnings: ${elimination_response.get('earnings', 0)}")
            else:
                print("❌ Failed to eliminate admin (winner)")
                return False
        
        # 8. Check game status to verify live eliminations
        print("\n--- VERIFYING LIVE ELIMINATIONS ---")
        _, final_game_status = self.test_get_game_status(league_id)
        if final_game_status:
            live_eliminations = final_game_status.get('live_eliminations', [])
            print(f"✅ Found {len(live_eliminations)} live eliminations")
            
            # Verify all positions are recorded
            positions = [e.get('finish_position') for e in live_eliminations]
            expected_positions = [1, 2, 3, 4, 5]
            
            if sorted(positions) == expected_positions:
                print("✅ All finish positions recorded correctly")
            else:
                print(f"❌ Expected positions {expected_positions}, got {sorted(positions)}")
                return False
            
            # Verify points calculation
            for elimination in live_eliminations:
                pos = elimination.get('finish_position')
                points = elimination.get('points_earned')
                print(f"   Position {pos}: {elimination.get('user_name')} - {points} points")
                
                # Verify points match expected calculation
                expected_points = 100 if pos == 1 else 80 if pos == 2 else 60 if pos == 3 else 40 if pos <= 5 else 20
                if points != expected_points:
                    print(f"❌ Expected {expected_points} points for position {pos}, got {points}")
                    return False
            
            print("✅ All points calculated correctly")
            
            # Verify eliminated count
            eliminated_count = final_game_status.get('eliminated_count', 0)
            if eliminated_count == 5:
                print("✅ Eliminated count is correct")
            else:
                print(f"❌ Expected 5 eliminated players, got {eliminated_count}")
                return False
            
            # Verify active players count (should be 0 now)
            active_count = final_game_status.get('checked_in_players', 0)
            if active_count == 0:
                print("✅ No active players remaining")
            else:
                print(f"❌ Expected 0 active players, got {active_count}")
                return False
        
        # 9. Check leaderboard to verify real-time updates
        print("\n--- VERIFYING LEADERBOARD UPDATES ---")
        leaderboard_success, leaderboard = self.test_get_league_leaderboard(league_id)
        if not leaderboard_success:
            print("❌ Failed to get league leaderboard")
            return False
        
        if len(leaderboard) != 5:
            print(f"❌ Expected 5 players on leaderboard, got {len(leaderboard)}")
            return False
        else:
            print(f"✅ Leaderboard has correct number of players: {len(leaderboard)}")
        
        # Verify winner is at top
        winner = leaderboard[0]
        if winner.get('user_name') == admin.get('name'):
            print(f"✅ Winner {winner.get('user_name')} is at top of leaderboard")
            print(f"   Points: {winner.get('total_points')}")
            print(f"   Earnings: ${winner.get('total_earnings')}")
        else:
            print(f"❌ Expected {admin.get('name')} at top, got {winner.get('user_name')}")
            return False
        
        # 10. Test error handling - try to use duplicate position
        print("\n--- TESTING ERROR HANDLING ---")
        
        # Reset game first
        reset_success, _ = self.test_reset_game(league_id)
        if not reset_success:
            print("❌ Failed to reset game for error testing")
            return False
        
        # Check in 2 players and start game
        for user in [admin, test_users[0]]:
            login_success, _ = self.test_login_user(user.get('email'))
            if login_success:
                self.test_player_checkin(league_id)
        
        # Start game as admin
        login_success, _ = self.test_login_user(admin_email)
        if login_success:
            self.test_start_game(league_id)
        
        # First player eliminates in 2nd place
        login_success, _ = self.test_login_user(test_users[0].get('email'))
        if login_success:
            self.test_player_checkin(league_id, action="check_out", finish_position=2)
        
        # Try to eliminate admin in same position (should fail)
        login_success, _ = self.test_login_user(admin_email)
        if login_success:
            # This should fail because position 2 is already taken
            duplicate_success, _ = self.run_test(
                "Duplicate Position Test (should fail)",
                "POST",
                f"api/game/{league_id}/checkin",
                400,  # Expecting error
                data={
                    "league_id": league_id,
                    "action": "check_out",
                    "finish_position": 2
                },
                auth=True
            )
            
            if duplicate_success:
                print("✅ Duplicate position correctly rejected")
            else:
                print("❌ Duplicate position should have been rejected")
        
        print("✅ Real-time score logging flow test completed successfully!")
        return True

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
        
        # 4. First get game status to initialize the game
        _, game_status = self.test_get_game_status(league_id)
        if not game_status:
            print("❌ Failed to get initial game status")
            return False
            
        print("✅ Game initialized successfully")
        
        # 5. Check-in all users (admin + test users)
        for user in [admin] + test_users:
            # Login as this user
            login_success, _ = self.test_login_user(user.get('email'))
            if login_success:
                # Check in
                checkin_success, _ = self.test_player_checkin(league_id)
                if not checkin_success:
                    print(f"❌ Failed to check in user {user.get('name')}")
                else:
                    print(f"✅ Checked in user {user.get('name')}")
        
        # 6. Login as admin and start the game
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
        
        # 7. Complete the game with results
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
        
        # 8. Check leaderboard
        leaderboard_success, leaderboard = self.test_get_league_leaderboard(league_id)
        if not leaderboard_success:
            print("❌ Failed to get league leaderboard")
            return False
        
        if len(leaderboard) != len(all_players):
            print(f"❌ Expected {len(all_players)} players on leaderboard, got {len(leaderboard)}")
        else:
            print(f"✅ Leaderboard has correct number of players: {len(leaderboard)}")
        
        # 9. Check overall leaderboard
        overall_success, _ = self.test_get_overall_leaderboard()
        if not overall_success:
            print("❌ Failed to get overall leaderboard")
            return False
        
        # 10. Check user stats for winner
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
        
        # 11. Reset the game
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
    
    # Test the NEW Real-Time Score Logging feature
    tester.test_real_time_score_logging_flow()
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())