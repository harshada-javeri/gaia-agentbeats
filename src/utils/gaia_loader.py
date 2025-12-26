"""GAIA dataset loader with Hugging Face integration."""

import os
from pathlib import Path
from typing import Dict, Any, List
from datasets import load_dataset
from huggingface_hub import snapshot_download
import dotenv

dotenv.load_dotenv()


class GAIADatasetLoader:
    """Loads and manages GAIA benchmark dataset."""

    def __init__(self, cache_dir: str | None = None):
        """Initialize GAIA dataset loader.

        Args:
            cache_dir: Optional directory to cache dataset files
        """
        self.cache_dir = cache_dir or os.path.join(
            Path.home(), ".cache", "agentbeats-gaia"
        )
        self.dataset_repo = "gaia-benchmark/GAIA"
        self._datasets = {}

    def _get_split_name(self, level: int, split: str) -> str:
        """Convert level and split to GAIA dataset split name.

        Args:
            level: Difficulty level (1, 2, or 3)
            split: 'validation' or 'test'

        Returns:
            Dataset split name like '2023_level1'
        """
        if level not in [1, 2, 3]:
            raise ValueError(f"Level must be 1, 2, or 3, got {level}")
        if split not in ["validation", "test"]:
            raise ValueError(f"Split must be 'validation' or 'test', got {split}")

        return f"2023_level{level}"

    def load_dataset(self, level: int = 1, split: str = "validation") -> Any:
        """Load GAIA dataset for a specific level and split.

        Args:
            level: Difficulty level (1, 2, or 3)
            split: 'validation' or 'test'

        Returns:
            Loaded dataset

        Raises:
            ValueError: If HF_TOKEN not set in environment
        """
        if not os.getenv("HF_TOKEN"):
            raise ValueError(
                "HF_TOKEN environment variable required. "
                "Get access at: https://huggingface.co/datasets/gaia-benchmark/GAIA"
            )

        split_name = self._get_split_name(level, split)
        cache_key = f"{split_name}_{split}"

        if cache_key not in self._datasets:
            print(f"Loading GAIA dataset: {split_name} ({split} split)...")

            # Download dataset repository
            data_dir = snapshot_download(
                repo_id=self.dataset_repo,
                repo_type="dataset",
                cache_dir=self.cache_dir,
                token=os.getenv("HF_TOKEN"),
            )

            # Load the specific split
            dataset = load_dataset(data_dir, split_name, split=split)
            self._datasets[cache_key] = dataset
            print(f"Loaded {len(dataset)} examples from {split_name}")

        return self._datasets[cache_key]

    def get_task(self, level: int, split: str, task_index: int) -> Dict[str, Any]:
        """Get a specific task by index.

        Args:
            level: Difficulty level (1, 2, or 3)
            split: 'validation' or 'test'
            task_index: Index of the task in the dataset

        Returns:
            Task dictionary with fields:
                - task_id: Unique task identifier
                - Question: The question to answer
                - Level: Difficulty level
                - Final answer: Ground truth answer (may be hidden for test split)
                - file_name: Name of associated file (if any)
                - file_path: Path to associated file (if any)
                - Annotator Metadata: Additional metadata
        """
        dataset = self.load_dataset(level, split)

        if task_index >= len(dataset):
            raise IndexError(
                f"Task index {task_index} out of range for dataset with {len(dataset)} examples"
            )

        return dict(dataset[task_index])

    def get_task_batch(
        self, level: int, split: str, task_indices: List[int]
    ) -> List[Dict[str, Any]]:
        """Get multiple tasks by their indices.

        Args:
            level: Difficulty level (1, 2, or 3)
            split: 'validation' or 'test'
            task_indices: List of task indices

        Returns:
            List of task dictionaries
        """
        return [self.get_task(level, split, idx) for idx in task_indices]


if __name__ == "__main__":
    # Example usage
    loader = GAIADatasetLoader()
    task = loader.get_task(level=1, split="validation", task_index=0)
    print("Sample GAIA task:")
    print(f"Question: {task['Question']}")
    print(f"Level: {task['Level']}")
    print(f"Task ID: {task.get('task_id', 'N/A')}")
