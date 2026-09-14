class PipelineError(Exception):
    """Hard failure in the data pipeline; the file cannot produce a CleanLedger."""
