"""
Scratch script to test CTC model architecture loading and LayerNorm gradient flow.
"""
import torch
import torch.nn as nn
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC, HubertForCTC, Data2VecAudioForCTC

def test_arch(name, model_cls, model_id):
    print(f"\nTesting {name} ({model_id})...")
    try:
        model = model_cls.from_pretrained(model_id)
        ln_params = []
        for n, m in model.named_modules():
            if isinstance(m, nn.LayerNorm) or "layer_norm" in n.lower():
                for p_n, p in m.named_parameters(recurse=False):
                    p.requires_grad = True
                    ln_params.append(p)
        ln_params = list({id(p): p for p in ln_params}.values())
        print(f"  Found {len(ln_params)} LayerNorm trainable parameters.")
        
        # Test dummy forward pass
        dummy_input = torch.randn(1, 16000)
        out = model(dummy_input)
        logits = out.logits
        print(f"  Logits shape: {logits.shape}")
        
        # Test backward pass
        probs = torch.softmax(logits / 2.5, dim=-1)
        loss = -torch.mean(torch.sum(probs * torch.log(probs + 1e-8), dim=-1))
        loss.backward()
        grads = [p.grad is not None for p in ln_params]
        print(f"  Gradient flow verified: {sum(grads)}/{len(ln_params)} params received grads.")
        print(f"  SUCCESS for {name}!")
    except Exception as e:
        print(f"  ERROR for {name}: {e}")

if __name__ == "__main__":
    # Test Data2Vec
    test_arch("data2vec_audio", Data2VecAudioForCTC, "facebook/data2vec-audio-base-960h")
