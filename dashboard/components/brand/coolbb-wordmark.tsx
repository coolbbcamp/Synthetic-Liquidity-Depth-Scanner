import Image from "next/image";

const COOLBB_SITE = "https://coolbb.site";

type CoolBBWordmarkProps = {
  className?: string;
};

export function CoolBBWordmark({ className = "" }: CoolBBWordmarkProps) {
  return (
    <a
      href={COOLBB_SITE}
      target="_blank"
      rel="noopener noreferrer"
      className={`coolbb-wordmark ${className}`.trim()}
      aria-label="CoolBB official site"
    >
      <Image
        src="/coolbb-logo.png"
        alt=""
        width={72}
        height={72}
        className="coolbb-wordmark__logo"
        priority
      />
      <span className="coolbb-wordmark__text">
        <span className="coolbb-wordmark__cool">Cool</span>
        <span className="coolbb-wordmark__bb">BB</span>
      </span>
    </a>
  );
}
