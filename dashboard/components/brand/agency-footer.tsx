import Image from "next/image";

type AgencyFooterProps = {
  builtBy: string;
  tagline: string;
  contactX: string;
  website: string;
  provenance: string;
  disclaimer: string;
};

export function AgencyFooter({
  builtBy,
  tagline,
  contactX,
  website,
  provenance,
  disclaimer,
}: AgencyFooterProps) {
  return (
    <footer className="site-footer agency-footer">
      <div className="container container--wide">
        <div className="agency-footer__layout">
          <div className="agency-footer__copy">
            <p className="agency-footer__built-by">{builtBy}</p>
            <p className="agency-footer__tagline">{tagline}</p>
            <p className="agency-footer__links">
              <a href="https://coolbb.site" target="_blank" rel="noopener noreferrer">
                {website}
              </a>
              <span className="agency-footer__sep" aria-hidden="true">·</span>
              <a href="https://x.com/coolBilliBigBoy" target="_blank" rel="noopener noreferrer">
                {contactX}
              </a>
            </p>
            <hr className="hairline agency-footer__rule" />
            <p>{provenance}</p>
            <p>{disclaimer}</p>
          </div>

          <a
            href="https://coolbb.site"
            target="_blank"
            rel="noopener noreferrer"
            className="agency-footer__frame"
            aria-label="CoolBB agency"
          >
            <Image
              src="/coolbb-agency.jpg"
              alt="CoolBB agency mascot"
              width={240}
              height={320}
              className="agency-footer__frame-img"
            />
          </a>
        </div>
      </div>
    </footer>
  );
}
