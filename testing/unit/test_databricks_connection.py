"""
Unit tests for Databricks connection utilities.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
import requests

from utils.databricks.connection import DatabricksConnection, DatabricksConfig


class TestDatabricksConfig:
    """Test Databricks configuration."""
    
    def test_config_initialization(self):
        """Test config initialization with valid parameters."""
        config = DatabricksConfig(
            host='https://test.databricks.com',
            token='test-token'
        )
        assert config.host == 'https://test.databricks.com'
        assert config.token == 'test-token'
        assert config.timeout == 30  # default timeout
    
    def test_config_with_custom_timeout(self):
        """Test config initialization with custom timeout."""
        config = DatabricksConfig(
            host='https://test.databricks.com',
            token='test-token',
            timeout=60
        )
        assert config.timeout == 60
    
    def test_config_validation_invalid_host(self):
        """Test config validation with invalid host."""
        with pytest.raises(ValueError, match="Host must start with https://"):
            DatabricksConfig(
                host='http://test.databricks.com',
                token='test-token'
            )
    
    def test_config_validation_empty_token(self):
        """Test config validation with empty token."""
        with pytest.raises(ValueError, match="Token cannot be empty"):
            DatabricksConfig(
                host='https://test.databricks.com',
                token=''
            )


class TestDatabricksConnection:
    """Test Databricks connection functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = DatabricksConfig(
            host='https://test.databricks.com',
            token='test-token'
        )
    
    def test_connection_initialization(self):
        """Test connection initialization."""
        conn = DatabricksConnection(self.config)
        assert conn.config == self.config
        assert conn.session is not None
    
    @patch('requests.Session')
    def test_connection_with_mocked_session(self, mock_session):
        """Test connection with mocked session."""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        
        conn = DatabricksConnection(self.config)
        
        assert conn.session == mock_session_instance
        mock_session_instance.headers.update.assert_called_once_with({
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json'
        })
    
    @patch('requests.Session')
    def test_get_clusters_success(self, mock_session):
        """Test successful cluster retrieval."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'clusters': [
                {'cluster_id': 'cluster1', 'state': 'RUNNING'},
                {'cluster_id': 'cluster2', 'state': 'TERMINATED'}
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        conn = DatabricksConnection(self.config)
        clusters = conn.get_clusters()
        
        assert len(clusters) == 2
        assert clusters[0]['cluster_id'] == 'cluster1'
        mock_session_instance.get.assert_called_once_with(
            'https://test.databricks.com/api/2.0/clusters/list',
            timeout=30
        )
    
    @patch('requests.Session')
    def test_get_clusters_api_error(self, mock_session):
        """Test cluster retrieval with API error."""
        # Setup mock response with error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("API Error")
        
        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        conn = DatabricksConnection(self.config)
        
        with pytest.raises(requests.HTTPError):
            conn.get_clusters()
    
    @patch('requests.Session')
    def test_get_cluster_details_success(self, mock_session):
        """Test successful cluster details retrieval."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'cluster_id': 'cluster1',
            'state': 'RUNNING',
            'driver': {'node_id': 'driver1'},
            'executors': [{'node_id': 'exec1'}]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        conn = DatabricksConnection(self.config)
        cluster_details = conn.get_cluster_details('cluster1')
        
        assert cluster_details['cluster_id'] == 'cluster1'
        assert cluster_details['state'] == 'RUNNING'
        mock_session_instance.get.assert_called_once_with(
            'https://test.databricks.com/api/2.0/clusters/get',
            params={'cluster_id': 'cluster1'},
            timeout=30
        )
    
    @patch('requests.Session')
    def test_start_cluster_success(self, mock_session):
        """Test successful cluster start."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {'cluster_id': 'cluster1'}
        mock_response.raise_for_status.return_value = None
        
        mock_session_instance = Mock()
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        conn = DatabricksConnection(self.config)
        result = conn.start_cluster('cluster1')
        
        assert result['cluster_id'] == 'cluster1'
        mock_session_instance.post.assert_called_once_with(
            'https://test.databricks.com/api/2.0/clusters/start',
            json={'cluster_id': 'cluster1'},
            timeout=30
        )
    
    @patch('requests.Session')
    def test_stop_cluster_success(self, mock_session):
        """Test successful cluster stop."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {'cluster_id': 'cluster1'}
        mock_response.raise_for_status.return_value = None
        
        mock_session_instance = Mock()
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        conn = DatabricksConnection(self.config)
        result = conn.stop_cluster('cluster1')
        
        assert result['cluster_id'] == 'cluster1'
        mock_session_instance.post.assert_called_once_with(
            'https://test.databricks.com/api/2.0/clusters/delete',
            json={'cluster_id': 'cluster1'},
            timeout=30
        )
    
    @patch('requests.Session')
    def test_run_job_success(self, mock_session):
        """Test successful job execution."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'run_id': 123,
            'state': {'life_cycle_state': 'PENDING'}
        }
        mock_response.raise_for_status.return_value = None
        
        mock_session_instance = Mock()
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        conn = DatabricksConnection(self.config)
        job_config = {
            'job_id': 456,
            'notebook_params': {'param1': 'value1'}
        }
        result = conn.run_job(job_config)
        
        assert result['run_id'] == 123
        mock_session_instance.post.assert_called_once_with(
            'https://test.databricks.com/api/2.0/jobs/run-now',
            json=job_config,
            timeout=30
        )
    
    @patch('requests.Session')
    def test_get_job_status_success(self, mock_session):
        """Test successful job status retrieval."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'run_id': 123,
            'state': {'life_cycle_state': 'TERMINATED', 'result_state': 'SUCCESS'}
        }
        mock_response.raise_for_status.return_value = None
        
        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        conn = DatabricksConnection(self.config)
        status = conn.get_job_status(123)
        
        assert status['run_id'] == 123
        assert status['state']['life_cycle_state'] == 'TERMINATED'
        mock_session_instance.get.assert_called_once_with(
            'https://test.databricks.com/api/2.0/jobs/runs/get',
            params={'run_id': 123},
            timeout=30
        )
    
    @patch('requests.Session')
    def test_upload_file_success(self, mock_session):
        """Test successful file upload."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {'path': '/FileStore/test_file.py'}
        mock_response.raise_for_status.return_value = None
        
        mock_session_instance = Mock()
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        conn = DatabricksConnection(self.config)
        
        # Create a mock file-like object
        mock_file = Mock()
        mock_file.read.return_value = b'print("hello world")'
        
        result = conn.upload_file(mock_file, '/FileStore/test_file.py')
        
        assert result['path'] == '/FileStore/test_file.py'
        mock_session_instance.post.assert_called_once()
    
    @patch('requests.Session')
    def test_download_file_success(self, mock_session):
        """Test successful file download."""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = b'print("hello world")'
        mock_response.raise_for_status.return_value = None
        
        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        conn = DatabricksConnection(self.config)
        content = conn.download_file('/FileStore/test_file.py')
        
        assert content == b'print("hello world")'
        mock_session_instance.get.assert_called_once_with(
            'https://test.databricks.com/api/2.0/workspace/export',
            params={'path': '/FileStore/test_file.py', 'format': 'SOURCE'},
            timeout=30
        )
    
    @patch('requests.Session')
    def test_list_workspace_success(self, mock_session):
        """Test successful workspace listing."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            'objects': [
                {'path': '/folder1', 'object_type': 'DIRECTORY'},
                {'path': '/notebook1.py', 'object_type': 'NOTEBOOK'}
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        conn = DatabricksConnection(self.config)
        objects = conn.list_workspace('/')
        
        assert len(objects) == 2
        assert objects[0]['path'] == '/folder1'
        mock_session_instance.get.assert_called_once_with(
            'https://test.databricks.com/api/2.0/workspace/list',
            params={'path': '/'},
            timeout=30
        )
    
    @patch('requests.Session')
    def test_connection_timeout_handling(self, mock_session):
        """Test connection timeout handling."""
        # Setup mock to raise timeout
        mock_session_instance = Mock()
        mock_session_instance.get.side_effect = requests.Timeout("Request timeout")
        mock_session.return_value = mock_session_instance
        
        conn = DatabricksConnection(self.config)
        
        with pytest.raises(requests.Timeout):
            conn.get_clusters()
    
    @patch('requests.Session')
    def test_connection_retry_mechanism(self, mock_session):
        """Test connection retry mechanism."""
        # Setup mock to fail first, then succeed
        mock_response = Mock()
        mock_response.json.return_value = {'clusters': []}
        mock_response.raise_for_status.return_value = None
        
        mock_session_instance = Mock()
        mock_session_instance.get.side_effect = [
            requests.ConnectionError("Connection error"),
            mock_response
        ]
        mock_session.return_value = mock_session_instance
        
        conn = DatabricksConnection(self.config)
        
        # This should raise the connection error since we don't have retry logic yet
        with pytest.raises(requests.ConnectionError):
            conn.get_clusters()
    
    def test_connection_context_manager(self):
        """Test connection as context manager."""
        with patch('requests.Session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value = mock_session_instance
            
            with DatabricksConnection(self.config) as conn:
                assert conn.config == self.config
                assert conn.session == mock_session_instance
            
            # Verify session was closed
            mock_session_instance.close.assert_called_once()
    
    def test_connection_authentication_headers(self):
        """Test that authentication headers are set correctly."""
        with patch('requests.Session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value = mock_session_instance
            
            conn = DatabricksConnection(self.config)
            
            # Verify headers were set
            mock_session_instance.headers.update.assert_called_once_with({
                'Authorization': 'Bearer test-token',
                'Content-Type': 'application/json'
            })
