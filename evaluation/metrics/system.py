def compute_inference_time(prediction):
    return prediction.inference_time_sec

def compute_success_rate(predictions):
    if not predictions:
        return 0.0
    success = sum(1 for p in predictions if p is not None)
    return success / len(predictions)
