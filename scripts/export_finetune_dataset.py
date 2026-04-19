"""Export user feedback as a LoRA/SFT fine-tune dataset.

Produces JSONL suitable for HuggingFace `autotrain` or `trl` SFTTrainer.
Each row = (user context, assistant reply, preference label).

Usage:
    python scripts/export_finetune_dataset.py > finetune/ro-sft.jsonl
    # then: autotrain llm --train --data finetune/ro-sft.jsonl --model meta-llama/Llama-3.2-1B
"""
import json
import os
import sys
from sqlalchemy import create_engine, text


def main():
    eng = create_engine(os.getenv("SYNC_DATABASE_URL",
                                  "postgresql://recuser:recpass@localhost:5432/recengine"))
    with eng.connect() as c:
        rows = c.execute(text("""
            SELECT cf.user_message, cf.assistant_message, cf.feedback,
                   u.dna_pace, u.dna_emotion, u.dna_darkness,
                   u.dna_humor, u.dna_complexity, u.dna_spectacle
            FROM chat_feedback cf JOIN users u ON u.id = cf.user_id
            WHERE cf.user_message IS NOT NULL AND cf.user_message <> ''
        """)).mappings().all()

    for r in rows:
        dna_desc = (
            f"pace={r['dna_pace']:.2f}, emotion={r['dna_emotion']:.2f}, "
            f"darkness={r['dna_darkness']:.2f}, humor={r['dna_humor']:.2f}, "
            f"complexity={r['dna_complexity']:.2f}, spectacle={r['dna_spectacle']:.2f}"
        )
        record = {
            "messages": [
                {"role": "system",
                 "content": f"You are RO, a personal recommender. Viewer DNA: {dna_desc}."},
                {"role": "user", "content": r["user_message"]},
                {"role": "assistant", "content": r["assistant_message"]},
            ],
            "label": int(r["feedback"]),  # +1 helpful, -1 not helpful
        }
        sys.stdout.write(json.dumps(record) + "\n")

    print(f"# exported {len(rows)} samples", file=sys.stderr)


if __name__ == "__main__":
    main()
