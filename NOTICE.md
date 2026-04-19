# NOTICE — Third-Party Attributions

RO AI Recommendation Engine is MIT-licensed original work by Rohith Kandula.
This file attributes third-party data, assets, and APIs used by the project.

## Content metadata & images

Movie/TV metadata (titles, descriptions, cast, posters, ratings) is pulled
at runtime from the following services and **is not owned by this project**:

### TVMaze
- Source: https://www.tvmaze.com/api
- License: [TVMaze Terms of Service](https://www.tvmaze.com/api#licensing)
- Usage: Non-commercial + commercial with attribution. No API key required.
- **Required attribution (displayed in UI):** "Show data provided by TVMaze."

### Trakt
- Source: https://trakt.tv/
- License: [Trakt API Agreement](https://trakt.docs.apiary.io/)
- Usage: Requires free API key. Must credit Trakt when displaying data.
- **Required attribution:** "Movie & TV data courtesy of Trakt."

### TMDB (The Movie Database)
- Source: https://www.themoviedb.org/
- License: [TMDB Terms of Use](https://www.themoviedb.org/terms-of-use)
- Usage: Free for non-commercial use. Commercial use requires written permission.
- **Required attribution + logo:** "This product uses the TMDB API but is not endorsed or certified by TMDB."

### OMDb
- Source: https://www.omdbapi.com/
- License: Free tier for non-commercial use (1000 req/day with key).
- **Required attribution:** "Rating data from OMDb."

### YouTube (trailer embeds)
- Source: https://www.youtube.com/
- License: [YouTube Terms of Service](https://www.youtube.com/t/terms)
- Usage: iframe embeds are permitted. Do not download or redistribute video.

## Open-source libraries

Major dependencies are each under permissive licenses (MIT/BSD/Apache-2.0):
- Next.js, React, TypeScript, Tailwind CSS, React Query, Zustand
- FastAPI, SQLAlchemy, Pydantic, Celery, Alembic, asyncpg, psycopg2
- PyTorch, FAISS (MIT), implicit (MIT), LightGBM (MIT), sentence-transformers (Apache-2.0)
- Redis, PostgreSQL, Kafka, ClickHouse — client libraries only

Full license texts: run `pip show <pkg>` / `npm info <pkg> license`.

## AI models

### OpenAI GPT-OSS (via OpenRouter)
- License: Apache-2.0
- Used for: chatbot, NL search parsing, spoiler-free rewrites, agent tool calls

### sentence-transformers/all-MiniLM-L6-v2
- License: Apache-2.0
- Used for: semantic search + content embeddings → FAISS

## Trademarks

- "Netflix" is a trademark of Netflix, Inc. This project is **unaffiliated with
  and not endorsed by Netflix**. The term "Netflix-style" is used descriptively
  to indicate UI patterns similar to theirs (rows, hover-expand, dark theme).
- The "RO" mark + animated intro are original work by this project.

## Seed data

The `scripts/real_content.json` curated set contains real movie/TV titles
(e.g. *The Shawshank Redemption*, *Inception*) whose factual metadata is not
copyrightable. Descriptions, where non-original, are either sourced from the
APIs above or are brief encyclopedic summaries that fall under fair-use
descriptive commentary.

## If you redistribute

1. Retain this `NOTICE.md` and the `LICENSE` file.
2. Obtain your own API keys for TVMaze/Trakt/TMDB/OMDb.
3. Do **not** cache/store images server-side; render them from the upstream CDN.
4. Remove or attribute the curated `real_content.json` titles per their source.
5. For commercial use of TMDB imagery, apply for commercial terms at themoviedb.org.

## Contact

Questions on attribution or takedown: rohithkandula937@gmail.com
