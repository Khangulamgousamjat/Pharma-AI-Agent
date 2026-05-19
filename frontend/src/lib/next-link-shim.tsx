import React from 'react';
import { Link as RRDLink } from 'react-router-dom';

interface LinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  href: string;
  replace?: boolean;
  prefetch?: boolean;
}

const Link = React.forwardRef<HTMLAnchorElement, LinkProps>(
  ({ href, replace, prefetch, ...props }, ref) => {
    return <RRDLink to={href} replace={replace} ref={ref} {...props} />;
  }
);

Link.displayName = 'Link';

export default Link;
export { Link };
