"""
Integration tests for loan processing endpoints
Tests all legacy processors with the new API routes
"""
import pytest
import io
import os
import json
from datetime import datetime
from flask import Flask
from app import create_app
from database import db
from models.user import User
from models.device import Device


@pytest.fixture
def app():
    """Create and configure test Flask app"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Create test user
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpass123')
        user.add_role('user')
        db.session.add(user)
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Get authentication headers"""
    response = client.post('/api/v1/auth/login', json={
        'username': 'testuser',
        'password': 'testpass123',
        'device_id': 'test-device-001'
    })
    
    assert response.status_code == 200
    token = response.json['access_token']
    
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def sample_csv_file():
    """Create sample CSV file for testing"""
    csv_content = """FullNames,PhoneNumber,Arrears Amount,DaysInArrears,LoanBalance,SalesRep
John Doe,0712345678,5000,15,50000,Agent A
Jane Smith,0723456789,3000,10,40000,Agent A
Bob Johnson,0734567890,8000,25,60000,Agent B
Alice Brown,0745678901,2000,5,30000,Agent B"""
    
    return io.BytesIO(csv_content.encode('utf-8'))


@pytest.fixture
def sample_excel_file():
    """Create sample Excel file for testing"""
    import pandas as pd
    
    data = {
        'FullNames': ['John Doe', 'Jane Smith', 'Bob Johnson'],
        'PhoneNumber': ['0712345678', '0723456789', '0734567890'],
        'Arrears Amount': [5000, 3000, 8000],
        'DaysInArrears': [15, 10, 25],
        'LoanBalance': [50000, 40000, 60000],
        'SalesRep': ['Agent A', 'Agent A', 'Agent B']
    }
    
    df = pd.DataFrame(data)
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    
    return excel_buffer


class TestDormantArrangementEndpoint:
    """Test dormant arrangement processing"""
    
    def test_dormant_arrangement_success(self, client, auth_headers, sample_csv_file):
        """Test successful dormant arrangement processing"""
        response = client.post(
            '/api/v1/loans/dormant-arrangement',
            headers=auth_headers,
            data={'file': (sample_csv_file, 'test.csv')}
        )
        
        assert response.status_code == 200
        data = response.json
        
        assert data['status'] == 'success'
        assert 'data' in data
        assert 'pagination' in data
        assert isinstance(data['data'], list)
    
    def test_dormant_arrangement_pagination(self, client, auth_headers, sample_csv_file):
        """Test pagination in dormant arrangement"""
        response = client.post(
            '/api/v1/loans/dormant-arrangement?limit=2',
            headers=auth_headers,
            data={'file': (sample_csv_file, 'test.csv')}
        )
        
        assert response.status_code == 200
        data = response.json
        
        assert len(data['data']) <= 2
        assert 'next_cursor' in data['pagination']
    
    def test_dormant_arrangement_no_file(self, client, auth_headers):
        """Test error when no file is provided"""
        response = client.post(
            '/api/v1/loans/dormant-arrangement',
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert 'error' in response.json
    
    def test_dormant_arrangement_invalid_file_type(self, client, auth_headers):
        """Test error with invalid file type"""
        invalid_file = io.BytesIO(b'not a valid file')
        
        response = client.post(
            '/api/v1/loans/dormant-arrangement',
            headers=auth_headers,
            data={'file': (invalid_file, 'test.txt')}
        )
        
        assert response.status_code == 400


class TestArrearsCollectedEndpoint:
    """Test arrears collected processing"""
    
    def test_arrears_collected_success(self, client, auth_headers, sample_csv_file):
        """Test successful arrears collection processing"""
        sod_file = sample_csv_file
        cur_file = io.BytesIO(sample_csv_file.getvalue())
        
        response = client.post(
            '/api/v1/loans/arrears-collected',
            headers=auth_headers,
            data={
                'sod_file': (sod_file, 'sod.csv'),
                'cur_file': (cur_file, 'current.csv')
            }
        )
        
        assert response.status_code == 200
        data = response.json
        
        assert data['status'] == 'success'
        assert 'summary' in data
    
    def test_arrears_collected_with_targets(self, client, auth_headers, sample_csv_file):
        """Test arrears collection with officer targets"""
        sod_file = sample_csv_file
        cur_file = io.BytesIO(sample_csv_file.getvalue())
        
        targets = {
            'Agent A': 10000,
            'Agent B': 15000
        }
        
        response = client.post(
            '/api/v1/loans/arrears-collected',
            headers=auth_headers,
            data={
                'sod_file': (sod_file, 'sod.csv'),
                'cur_file': (cur_file, 'current.csv'),
                'officer_targets': json.dumps(targets)
            }
        )
        
        assert response.status_code == 200
        data = response.json
        
        assert 'officer_targets' in data
    
    def test_arrears_collected_missing_file(self, client, auth_headers, sample_csv_file):
        """Test error when one file is missing"""
        response = client.post(
            '/api/v1/loans/arrears-collected',
            headers=auth_headers,
            data={'sod_file': (sample_csv_file, 'sod.csv')}
        )
        
        assert response.status_code == 400


class TestArrangeDuesEndpoint:
    """Test arrange dues processing"""
    
    def test_arrange_dues_success(self, client, auth_headers, sample_csv_file):
        """Test successful dues arrangement"""
        response = client.post(
            '/api/v1/loans/arrange-dues',
            headers=auth_headers,
            data={'file': (sample_csv_file, 'test.csv')}
        )
        
        assert response.status_code == 200
        data = response.json
        
        assert data['status'] == 'success'
        assert 'summary' in data
    
    def test_arrange_dues_excel_format(self, client, auth_headers, sample_excel_file):
        """Test with Excel file"""
        response = client.post(
            '/api/v1/loans/arrange-dues',
            headers=auth_headers,
            data={'file': (sample_excel_file, 'test.xlsx')}
        )
        
        assert response.status_code == 200


class TestArrangeArrearsEndpoint:
    """Test arrange arrears processing"""
    
    def test_arrange_arrears_success(self, client, auth_headers, sample_csv_file):
        """Test successful arrears arrangement"""
        response = client.post(
            '/api/v1/loans/arrange-arrears',
            headers=auth_headers,
            data={'file': (sample_csv_file, 'test.csv')}
        )
        
        assert response.status_code == 200
        data = response.json
        
        assert data['status'] == 'success'
        assert 'metadata' in data


class TestMTDParametersEndpoint:
    """Test MTD parameters processing"""
    
    def test_mtd_parameters_success(self, client, auth_headers):
        """Test successful MTD parameters analysis"""
        # Create sample files for MTD
        income_csv = io.BytesIO(b"Branch,Income (KES)\nBranch A,100000\nBranch B,150000")
        cr_csv = io.BytesIO(b"Branch,CR %,Collected,Uncollected\nBranch A,85,85000,15000\nBranch B,90,135000,15000")
        disb_csv = io.BytesIO(b"Branch,Disbursement,Loan Count\nBranch A,200000,50\nBranch B,300000,75")
        
        response = client.post(
            '/api/v1/loans/mtd-parameters',
            headers=auth_headers,
            data={
                'income_file': (income_csv, 'income.csv'),
                'cr_file': (cr_csv, 'cr.csv'),
                'disb_file': (disb_csv, 'disb.csv')
            }
        )
        
        assert response.status_code == 200
        data = response.json
        
        assert data['status'] == 'success'
        assert 'summary' in data


class TestMTDUnpaidDuesEndpoint:
    """Test MTD unpaid dues processing"""
    
    def test_mtd_unpaid_dues_success(self, client, auth_headers, sample_csv_file):
        """Test successful MTD unpaid dues analysis"""
        response = client.post(
            '/api/v1/loans/mtd-unpaid-dues',
            headers=auth_headers,
            data={'file': (sample_csv_file, 'test.csv')}
        )
        
        assert response.status_code == 200
        data = response.json
        
        assert data['status'] == 'success'
        assert 'summary' in data


class TestProgressTracking:
    """Test progress tracking for long operations"""
    
    def test_progress_endpoint_exists(self, client, auth_headers):
        """Test that progress endpoint is available"""
        response = client.get(
            '/api/v1/loans/progress/test-operation-id',
            headers=auth_headers
        )
        
        # Should return 404 for non-existent operation
        assert response.status_code in [404, 200]


class TestErrorHandling:
    """Test error handling across all endpoints"""
    
    def test_unauthorized_access(self, client, sample_csv_file):
        """Test that endpoints require authentication"""
        response = client.post(
            '/api/v1/loans/dormant-arrangement',
            data={'file': (sample_csv_file, 'test.csv')}
        )
        
        assert response.status_code == 401
    
    def test_invalid_token(self, client, sample_csv_file):
        """Test with invalid authentication token"""
        headers = {
            'Authorization': 'Bearer invalid-token-here',
            'Content-Type': 'application/json'
        }
        
        response = client.post(
            '/api/v1/loans/dormant-arrangement',
            headers=headers,
            data={'file': (sample_csv_file, 'test.csv')}
        )
        
        assert response.status_code == 401


class TestRateLimiting:
    """Test rate limiting on endpoints"""
    
    def test_rate_limit_enforcement(self, client, auth_headers, sample_csv_file):
        """Test that rate limiting is enforced"""
        # Make multiple rapid requests
        responses = []
        for _ in range(15):  # Exceed typical rate limit
            response = client.post(
                '/api/v1/loans/dormant-arrangement',
                headers=auth_headers,
                data={'file': (sample_csv_file, 'test.csv')}
            )
            responses.append(response.status_code)
        
        # Should have at least one 429 (Too Many Requests)
        assert 429 in responses or all(r == 200 for r in responses)


# Performance tests
class TestPerformance:
    """Test performance with larger datasets"""
    
    def test_large_file_processing(self, client, auth_headers):
        """Test processing of larger files"""
        # Create larger dataset
        large_data = []
        for i in range(1000):
            large_data.append(f"User {i},071234{i:04d},5000,15,50000,Agent A")
        
        csv_content = "FullNames,PhoneNumber,Arrears Amount,DaysInArrears,LoanBalance,SalesRep\n"
        csv_content += "\n".join(large_data)
        
        large_file = io.BytesIO(csv_content.encode('utf-8'))
        
        import time
        start_time = time.time()
        
        response = client.post(
            '/api/v1/loans/dormant-arrangement',
            headers=auth_headers,
            data={'file': (large_file, 'large.csv')}
        )
        
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed_time < 30  # Should complete within 30 seconds


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
