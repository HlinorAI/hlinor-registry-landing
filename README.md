# Hlinor Agent Registry — landing page

Single static page served at [registry.hlinor.com](https://registry.hlinor.com)
by the Cloudflare Worker `morning-violet-5f09` (static assets only). The product
itself lives in
[HlinorAI/hlinor-agent-registry](https://github.com/HlinorAI/hlinor-agent-registry)
(PyPI: [`hlinor-registry`](https://pypi.org/project/hlinor-registry/)).

## Deployment

The page is deployed with Wrangler from a logged-in machine:

```bash
npx wrangler deploy
```

`wrangler.jsonc` binds the deploy to the Worker `morning-violet-5f09`, which owns
the custom domain `registry.hlinor.com`. `.assetsignore` publishes only
`index.html`; the rest of the repository is never uploaded. A push to `main`
does not deploy anything: deploy after the change is merged.

Preview locally with `npx wrangler dev`.

GitHub Pages is not enabled for this repository. `CNAME` and `.nojekyll` are
left over from that setup; `CNAME` is still checked by CI as the canonical host.

Cloudflare Web Analytics on the `hlinor.com` zone injects its beacon script into
pages served at the edge, including this one. That script is not part of
`index.html` and is not caught by `check_external_resources.py`. To keep the
"no third-party runtime code" guarantee on the live page, exclude
`registry.hlinor.com` from Web Analytics in the Cloudflare dashboard.

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
