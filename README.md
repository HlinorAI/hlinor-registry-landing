# Hlinor Agent Registry — landing page

Single static page served at [registry.hlinor.com](https://registry.hlinor.com)
via GitHub Pages. The product itself lives in
[HlinorAI/hlinor-agent-registry](https://github.com/HlinorAI/hlinor-agent-registry)
(PyPI: [`hlinor-registry`](https://pypi.org/project/hlinor-registry/)).

## Deployment

GitHub Pages from `main` with the custom domain from `CNAME`.
`.nojekyll` keeps the page served as-is.

## Editing the page

The page has **no third-party runtime dependency**: Tailwind CSS and Prism are
built and vendored inline, so the public face of a governance tool never
executes unverified third-party code on a visitor's machine.

To change markup, edit `index.html`, then rebuild the inline assets with the
script in the product repo and paste the four blocks into `index.html`:

```bash
bash ../hlinor-agent-registry/scripts/build_landing_assets.sh
```

The CI workflow (`validate.yml`) fails if an external `<script src>` or
stylesheet ever creeps back in, if `CNAME` stops matching the canonical URL,
or if the HTML stops validating.

## License

Apache-2.0, same as the product repo.
