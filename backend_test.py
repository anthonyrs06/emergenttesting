import requests
import unittest
import sys
import os

class PokerLeagueAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
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
                return success, response.json()
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                return success, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_get_players(self):
        """Test getting the list of players"""
        success, response = self.run_test(
            "Get Players",
            "GET",
            "api/players",
            200
        )
        if success:
            print(f"Retrieved {len(response)} players")
            if len(response) == 15:
                print("✅ Correct number of players (15)")
            else:
                print(f"❌ Expected 15 players, got {len(response)}")
        return success

    def test_get_game_status(self):
        """Test getting the current game status"""
        success, response = self.run_test(
            "Get Game Status",
            "GET",
            "api/game/status",
            200
        )
        if success:
            print(f"Game status: {len(response.get('seat_assignments', []))} players checked in")
            print(f"Tables needed: {response.get('tables_needed', 0)}")
        return success, response

    def test_player_checkin(self, player_id):
        """Test checking in a player"""
        success, response = self.run_test(
            f"Check In Player {player_id}",
            "POST",
            "api/game/checkin",
            200,
            data={"player_id": player_id, "action": "check_in"}
        )
        if success:
            print(f"Player checked in: {response.get('message', '')}")
            print(f"Total checked in: {response.get('checked_in_count', 0)}")
        return success

    def test_player_checkout(self, player_id):
        """Test checking out a player"""
        success, response = self.run_test(
            f"Check Out Player {player_id}",
            "POST",
            "api/game/checkin",
            200,
            data={"player_id": player_id, "action": "check_out"}
        )
        if success:
            print(f"Player checked out: {response.get('message', '')}")
            print(f"Total checked in: {response.get('checked_in_count', 0)}")
        return success

    def test_start_game(self):
        """Test starting the game"""
        success, response = self.run_test(
            "Start Game",
            "POST",
            "api/game/start",
            200,
            data={}
        )
        if success:
            print(f"Game started: {response.get('message', '')}")
        return success

    def test_reset_game(self):
        """Test resetting the game"""
        success, response = self.run_test(
            "Reset Game",
            "POST",
            "api/game/reset",
            200,
            data={}
        )
        if success:
            print(f"Game reset: {response.get('message', '')}")
        return success

    def test_seat_assignment_algorithm(self):
        """Test the seat assignment algorithm with different player counts"""
        print("\n🔍 Testing Seat Assignment Algorithm...")
        
        # Reset game first
        self.test_reset_game()
        
        # Test with 1-9 players (should be 1 table)
        print("\n--- Testing with 1-9 players (should be 1 table) ---")
        for i in range(1, 10):
            self.test_player_checkin(f"player{i}")
            _, status = self.test_get_game_status()
            tables_needed = status.get('tables_needed', 0)
            if tables_needed == 1:
                print(f"✅ With {i} players: {tables_needed} table needed (correct)")
            else:
                print(f"❌ With {i} players: {tables_needed} tables needed (expected 1)")
        
        # Test with 10+ players (should be multiple tables)
        print("\n--- Testing with 10+ players (should be multiple tables) ---")
        for i in range(10, 16):
            self.test_player_checkin(f"player{i}")
            _, status = self.test_get_game_status()
            tables_needed = status.get('tables_needed', 0)
            expected_tables = (i + 8) // 9  # Same formula as in the backend
            if tables_needed == expected_tables:
                print(f"✅ With {i} players: {tables_needed} tables needed (correct)")
            else:
                print(f"❌ With {i} players: {tables_needed} tables needed (expected {expected_tables})")
        
        # Check distribution across tables
        _, status = self.test_get_game_status()
        seat_assignments = status.get('seat_assignments', [])
        
        # Count players per table
        table_counts = {}
        for seat in seat_assignments:
            table_num = seat.get('table_number')
            if table_num not in table_counts:
                table_counts[table_num] = 0
            table_counts[table_num] += 1
        
        # Check if distribution is even (max difference should be 1)
        if table_counts:
            min_players = min(table_counts.values())
            max_players = max(table_counts.values())
            if max_players - min_players <= 1:
                print(f"✅ Even distribution across tables: {table_counts}")
            else:
                print(f"❌ Uneven distribution across tables: {table_counts}")
        
        # Reset game after testing
        self.test_reset_game()
        
        return True

def main():
    # Get backend URL from frontend .env
    backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'https://a9a27050-24da-4065-a659-67dc159b3097.preview.emergentagent.com')
    
    print(f"Testing against backend URL: {backend_url}")
    
    # Setup
    tester = PokerLeagueAPITester(backend_url)
    
    # Run tests
    print("\n=== POKER LEAGUE API TESTS ===")
    
    # Basic API tests
    tester.test_get_players()
    tester.test_get_game_status()
    
    # Player check-in/out tests
    tester.test_player_checkin("player1")
    tester.test_player_checkin("player2")
    tester.test_player_checkout("player1")
    
    # Game control tests
    tester.test_player_checkin("player1")  # Need at least 2 players to start
    tester.test_start_game()
    tester.test_reset_game()
    
    # Algorithm tests
    tester.test_seat_assignment_algorithm()
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())