"""
Databricks connection management.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

from ..common.exceptions import APIError, ConfigurationError
from ..common.logging import get_logger


@dataclass
class DatabricksConfig:
    """Databricks configuration."""

    host: str
    token: str
    cluster_id: Optional[str] = None
    workspace_id: Optional[str] = None
    catalog: str = "main"
    schema: str = "default"


class DatabricksConnection:
    """Databricks connection manager."""

    def __init__(self, config: DatabricksConfig):
        """
        Initialize Databricks connection.

        Args:
            config: Databricks configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {config.token}",
                "Content-Type": "application/json",
            }
        )

    def test_connection(self) -> bool:
        """
        Test connection to Databricks workspace.

        Returns:
            True if connection is successful
        """
        try:
            response = self._session.get(f"{self.config.host}/api/2.0/clusters/list")
            response.raise_for_status()
            self.logger.info("Successfully connected to Databricks workspace")
            return True
        except requests.RequestException as e:
            self.logger.error(f"Failed to connect to Databricks: {str(e)}")
            return False

    def get_clusters(self) -> List[Dict[str, Any]]:
        """
        Get list of clusters.

        Returns:
            List of cluster information
        """
        try:
            response = self._session.get(f"{self.config.host}/api/2.0/clusters/list")
            response.raise_for_status()
            data = response.json()
            clusters = data.get("clusters", [])
            if not isinstance(clusters, list):
                return []
            return clusters
        except requests.RequestException as e:
            raise APIError(
                f"Failed to get clusters: {str(e)}", endpoint="/api/2.0/clusters/list"
            )

    def get_cluster_info(self, cluster_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get cluster information.

        Args:
            cluster_id: Cluster ID (uses config cluster_id if not provided)

        Returns:
            Cluster information
        """
        cluster_id = cluster_id or self.config.cluster_id
        if not cluster_id:
            raise ConfigurationError("Cluster ID not provided")

        try:
            response = self._session.get(
                f"{self.config.host}/api/2.0/clusters/get",
                params={"cluster_id": cluster_id},
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                return {}
            return data
        except requests.RequestException as e:
            raise APIError(
                f"Failed to get cluster info: {str(e)}",
                endpoint="/api/2.0/clusters/get",
            )

    def start_cluster(self, cluster_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Start a cluster.

        Args:
            cluster_id: Cluster ID (uses config cluster_id if not provided)

        Returns:
            Start cluster response
        """
        cluster_id = cluster_id or self.config.cluster_id
        if not cluster_id:
            raise ConfigurationError("Cluster ID not provided")

        try:
            response = self._session.post(
                f"{self.config.host}/api/2.0/clusters/start",
                json={"cluster_id": cluster_id},
            )
            response.raise_for_status()
            self.logger.info(f"Started cluster {cluster_id}")
            return response.json()
        except requests.RequestException as e:
            raise APIError(
                f"Failed to start cluster: {str(e)}", endpoint="/api/2.0/clusters/start"
            )

    def stop_cluster(self, cluster_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Stop a cluster.

        Args:
            cluster_id: Cluster ID (uses config cluster_id if not provided)

        Returns:
            Stop cluster response
        """
        cluster_id = cluster_id or self.config.cluster_id
        if not cluster_id:
            raise ConfigurationError("Cluster ID not provided")

        try:
            response = self._session.post(
                f"{self.config.host}/api/2.0/clusters/stop",
                json={"cluster_id": cluster_id},
            )
            response.raise_for_status()
            self.logger.info(f"Stopped cluster {cluster_id}")
            return response.json()
        except requests.RequestException as e:
            raise APIError(
                f"Failed to stop cluster: {str(e)}", endpoint="/api/2.0/clusters/stop"
            )

    def restart_cluster(self, cluster_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Restart a cluster.

        Args:
            cluster_id: Cluster ID (uses config cluster_id if not provided)

        Returns:
            Restart cluster response
        """
        cluster_id = cluster_id or self.config.cluster_id
        if not cluster_id:
            raise ConfigurationError("Cluster ID not provided")

        try:
            response = self._session.post(
                f"{self.config.host}/api/2.0/clusters/restart",
                json={"cluster_id": cluster_id},
            )
            response.raise_for_status()
            self.logger.info(f"Restarted cluster {cluster_id}")
            return response.json()
        except requests.RequestException as e:
            raise APIError(
                f"Failed to restart cluster: {str(e)}",
                endpoint="/api/2.0/clusters/restart",
            )

    def execute_sql(
        self, sql: str, warehouse_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute SQL query.

        Args:
            sql: SQL query to execute
            warehouse_id: SQL warehouse ID (optional)

        Returns:
            Query execution result
        """
        payload = {"statement": sql, "warehouse_id": warehouse_id}

        try:
            response = self._session.post(
                f"{self.config.host}/api/2.0/sql/statements", json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise APIError(
                f"Failed to execute SQL: {str(e)}", endpoint="/api/2.0/sql/statements"
            )

    def get_jobs(self) -> List[Dict[str, Any]]:
        """
        Get list of jobs.

        Returns:
            List of job information
        """
        try:
            response = self._session.get(f"{self.config.host}/api/2.0/jobs/list")
            response.raise_for_status()
            data = response.json()
            return data.get("jobs", [])
        except requests.RequestException as e:
            raise APIError(
                f"Failed to get jobs: {str(e)}", endpoint="/api/2.0/jobs/list"
            )

    def run_job(
        self, job_id: int, parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run a job.

        Args:
            job_id: Job ID to run
            parameters: Optional job parameters

        Returns:
            Job run response
        """
        payload = {"job_id": str(job_id)}
        if parameters:
            payload["notebook_params"] = parameters

        try:
            response = self._session.post(
                f"{self.config.host}/api/2.0/jobs/run-now", json=payload
            )
            response.raise_for_status()
            self.logger.info(f"Started job {job_id}")
            return response.json()
        except requests.RequestException as e:
            raise APIError(
                f"Failed to run job: {str(e)}", endpoint="/api/2.0/jobs/run-now"
            )

    def get_job_run(self, run_id: int) -> Dict[str, Any]:
        """
        Get job run information.

        Args:
            run_id: Job run ID

        Returns:
            Job run information
        """
        try:
            response = self._session.get(
                f"{self.config.host}/api/2.0/jobs/runs/get", params={"run_id": run_id}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise APIError(
                f"Failed to get job run: {str(e)}", endpoint="/api/2.0/jobs/runs/get"
            )

    def upload_file(self, file_path: str, target_path: str) -> Dict[str, Any]:
        """
        Upload file to Databricks workspace.

        Args:
            file_path: Local file path
            target_path: Target path in workspace

        Returns:
            Upload response
        """
        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                response = self._session.post(
                    f"{self.config.host}/api/2.0/workspace/import",
                    files=files,
                    data={"path": target_path, "format": "SOURCE"},
                )
                response.raise_for_status()
                self.logger.info(f"Uploaded file to {target_path}")
                return response.json()
        except requests.RequestException as e:
            raise APIError(
                f"Failed to upload file: {str(e)}", endpoint="/api/2.0/workspace/import"
            )

    def list_workspace(self, path: str = "/") -> List[Dict[str, Any]]:
        """
        List workspace contents.

        Args:
            path: Workspace path to list

        Returns:
            List of workspace items
        """
        try:
            response = self._session.get(
                f"{self.config.host}/api/2.0/workspace/list", params={"path": path}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("objects", [])
        except requests.RequestException as e:
            raise APIError(
                f"Failed to list workspace: {str(e)}",
                endpoint="/api/2.0/workspace/list",
            )


# Global connection instance
_connection_instance: Optional[DatabricksConnection] = None


def get_databricks_connection(
    config: Optional[DatabricksConfig] = None,
) -> DatabricksConnection:
    """
    Get global Databricks connection instance.

    Args:
        config: Optional Databricks configuration

    Returns:
        Databricks connection instance
    """
    global _connection_instance

    if config is not None:
        _connection_instance = DatabricksConnection(config)
    elif _connection_instance is None:
        from ..common.config import get_config

        app_config = get_config()
        databricks_config = DatabricksConfig(
            host=app_config.databricks.host,
            token=app_config.databricks.token,
            cluster_id=app_config.databricks.cluster_id,
            catalog=app_config.databricks.catalog,
            schema=app_config.databricks.schema,
        )
        _connection_instance = DatabricksConnection(databricks_config)

    return _connection_instance
