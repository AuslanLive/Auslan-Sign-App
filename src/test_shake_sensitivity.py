import json
import numpy as np
import os


def load_stats():
    with open(os.path.join('app', 'stats.json'), 'r') as f:
        stats = json.load(f)
    mu = np.array(stats['mean'], dtype=np.float32)
    sd = np.array(stats['std'], dtype=np.float32)
    sd[sd < 1e-6] = 1.0
    return mu, sd


def synth_word_sequence(base_amplitude: float = 0.2, timesteps: int = 48) -> np.ndarray:
    """
    Create a synthetic right/left hand trace (84 features) for 48 frames.
    Start with a simple smooth sine-like motion and optional jitter amplitude.
    Returns array of shape (timesteps, 84) in the same feature layout used by the server.
    """
    # 42 joints per hand (x,y)*21. We'll generate a wrist-centered trace.
    # Start with zeros and add a smooth component plus jitter.
    frames = []
    t = np.linspace(0.0, 2.0*np.pi, timesteps)
    for i in range(timesteps):
        # base smooth motion in x,y for all joints
        base_x = 0.5*np.sin(t[i])
        base_y = 0.5*np.cos(t[i])

        # make 21 identical joints per hand for simplicity
        left = np.tile([base_x, base_y], 21)
        right = np.tile([-base_x, base_y], 21)

        # stack left then right -> 84 features
        feat = np.concatenate([left, right]).astype(np.float32)

        # add jitter noise term
        jitter = np.random.normal(loc=0.0, scale=base_amplitude, size=feat.shape).astype(np.float32)
        frames.append(feat + jitter)

    return np.stack(frames, axis=0)  # (T,84)


def zscore(x: np.ndarray, mu: np.ndarray, sd: np.ndarray) -> np.ndarray:
    return (x - mu) / sd


def test_model_sensitivity_to_shake():
    """
    Non-destructive test: measure how top-1 probability changes as jitter increases.
    This does not assert anything, it prints results so humans can evaluate.
    """
    # Skip if model owner cannot be imported in this environment
    try:
        from app.school.video_to_text.Model_Owner import Model
    except Exception as e:
        print("Skipping test: cannot import Model due to:", e)
        return

    model_path = os.path.join('app', 'bilstm_best.keras')
    if not os.path.exists(model_path):
        print("Skipping test: model file not found at", model_path)
        return

    model = Model(model_path)
    mu, sd = load_stats()

    amplitudes = [0.0, 0.01, 0.05, 0.1, 0.2]
    print("Shake sensitivity probe (amplitude -> top1_prob, top1_label):")
    for amp in amplitudes:
        x = synth_word_sequence(base_amplitude=amp, timesteps=48)
        # Align to expected server flow: already wrist-centered and 48x84, so just z-score
        x_norm = zscore(x, mu, sd)
        x_batch = np.expand_dims(x_norm.astype(np.float32), axis=0)
        # get softmax
        import asyncio
        probs = asyncio.get_event_loop().run_until_complete(model.predict_from_normalized(x_batch))
        top_idx = int(np.argmax(probs))
        top_label = model.index_to_gloss[top_idx]
        top_prob = float(probs[top_idx])
        print(f"amp={amp:.3f} -> {top_prob:.4f} {top_label}")

    # Note: No assertions, purely observational as requested.


