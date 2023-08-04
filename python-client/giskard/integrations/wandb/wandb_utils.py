import contextlib
from typing import Optional


@contextlib.contextmanager
def wandb_run(project: Optional[str] = None, **kwargs):
    try:
        import wandb  # noqa
    except ImportError as e:
        raise ImportError("The 'wandb' python package is not installed. " "To get it, run 'pip install wandb'.") from e

    wandb.run = wandb.run or wandb.init(project=project or "giskard", **kwargs)
    wandb.run._label(repo="Giskard")  # noqa
    yield wandb.run