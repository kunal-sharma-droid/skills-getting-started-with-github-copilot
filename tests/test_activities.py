import pytest
from src.app import activities


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """
        Arrange: Activities pre-populated in memory
        Act: Get all activities
        Assert: Response status 200, contains all activities
        """
        # Arrange
        expected_count = len(activities)
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        assert len(response.json()) == expected_count
    
    def test_get_activities_contains_required_fields(self, client, reset_activities):
        """
        Arrange: Activities in database
        Act: Get activities
        Assert: Each activity contains required fields
        """
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        activities_data = response.json()
        
        # Assert
        for activity_name, activity_data in activities_data.items():
            assert required_fields.issubset(set(activity_data.keys())), \
                f"Activity {activity_name} missing required fields"
    
    def test_get_activities_participants_is_list(self, client, reset_activities):
        """
        Arrange: Activities endpoint
        Act: Get activities
        Assert: Participants field is always a list
        """
        # Arrange & Act
        response = client.get("/activities")
        activities_data = response.json()
        
        # Assert
        for activity_name, activity_data in activities_data.items():
            assert isinstance(activity_data["participants"], list), \
                f"Participants for {activity_name} is not a list"


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_successful_signup(self, client, reset_activities):
        """
        Arrange: Valid activity and new email
        Act: Post signup request
        Assert: Status 200, participant added, message correct
        """
        # Arrange
        activity_name = "Basketball Team"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert email in activities[activity_name]["participants"]
        assert "Signed up" in response.json()["message"]
    
    def test_signup_to_activity_with_existing_participants(self, client, reset_activities):
        """
        Arrange: Activity with existing participants and new email
        Act: Post signup
        Assert: New participant added, existing ones unchanged
        """
        # Arrange
        activity_name = "Chess Club"
        initial_count = len(activities[activity_name]["participants"])
        initial_participants = activities[activity_name]["participants"].copy()
        email = "newchess@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert len(activities[activity_name]["participants"]) == initial_count + 1
        for participant in initial_participants:
            assert participant in activities[activity_name]["participants"]
        assert email in activities[activity_name]["participants"]
    
    def test_duplicate_signup_returns_400(self, client, reset_activities):
        """
        Arrange: Already registered participant
        Act: Post signup with same email
        Assert: Status 400, error message about duplicate
        """
        # Arrange
        activity_name = "Chess Club"
        email = activities[activity_name]["participants"][0]
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_to_nonexistent_activity_returns_404(self, client, reset_activities):
        """
        Arrange: Non-existent activity name
        Act: Post signup request
        Assert: Status 404, activity not found message
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_response_message_format(self, client, reset_activities):
        """
        Arrange: Valid signup request
        Act: Post signup
        Assert: Response message contains email and activity name
        """
        # Arrange
        activity_name = "Swimming Club"
        email = "swimmer@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        message = response.json()["message"]
        
        # Assert
        assert response.status_code == 200
        assert email in message
        assert activity_name in message


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""
    
    def test_successful_unregister(self, client, reset_activities):
        """
        Arrange: Registered participant
        Act: Send delete request
        Assert: Status 200, participant removed, message correct
        """
        # Arrange
        activity_name = "Chess Club"
        email = activities[activity_name]["participants"][0]
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert email not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count - 1
        assert "Unregistered" in response.json()["message"]
    
    def test_unregister_nonexistent_participant_returns_400(self, client, reset_activities):
        """
        Arrange: Non-registered email
        Act: Send delete request
        Assert: Status 400, not signed up message
        """
        # Arrange
        activity_name = "Chess Club"
        email = "notstudent@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()
    
    def test_unregister_from_nonexistent_activity_returns_404(self, client, reset_activities):
        """
        Arrange: Non-existent activity
        Act: Send delete request
        Assert: Status 404
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_unregister_last_participant_leaves_empty_list(self, client, reset_activities):
        """
        Arrange: Activity with one participant
        Act: Delete that participant
        Assert: participants list is empty
        """
        # Arrange
        activity_name = "Basketball Team"
        email = "solo@mergington.edu"
        activities[activity_name]["participants"] = [email]
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert activities[activity_name]["participants"] == []
    
    def test_unregister_response_message_format(self, client, reset_activities):
        """
        Arrange: Registered participant
        Act: Delete participant
        Assert: Response message contains email and activity name
        """
        # Arrange
        activity_name = "Programming Class"
        email = activities[activity_name]["participants"][0]
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        message = response.json()["message"]
        
        # Assert
        assert response.status_code == 200
        assert email in message
        assert activity_name in message


class TestIntegration:
    """Integration tests combining multiple operations"""
    
    def test_signup_and_unregister_sequence(self, client, reset_activities):
        """
        Arrange: Empty activity
        Act: Signup, then unregister
        Assert: Participant added then removed
        """
        # Arrange
        activity_name = "Swimming Club"
        email = "swimmer@mergington.edu"
        
        # Act - Signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert - Signup
        assert signup_response.status_code == 200
        assert email in activities[activity_name]["participants"]
        
        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert - Unregister
        assert unregister_response.status_code == 200
        assert email not in activities[activity_name]["participants"]
    
    def test_multiple_signups_to_different_activities(self, client, reset_activities):
        """
        Arrange: Same email, multiple activities
        Act: Signup to multiple different activities
        Assert: Participant appears in all activities
        """
        # Arrange
        email = "versatile@mergington.edu"
        activities_to_join = ["Art Studio", "Drama Club", "Debate Team"]
        
        # Act & Assert for each signup
        for activity_name in activities_to_join:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
            assert email in activities[activity_name]["participants"]
    
    def test_get_activities_reflects_signup_changes(self, client, reset_activities):
        """
        Arrange: New signup
        Act: Post signup then get activities
        Assert: Updated participant count reflected
        """
        # Arrange
        activity_name = "Science Club"
        email = "scientist@mergington.edu"
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        # Act - Signup
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Act - Get activities again
        updated_response = client.get("/activities")
        
        # Assert
        updated_count = len(updated_response.json()[activity_name]["participants"])
        assert updated_count == initial_count + 1
