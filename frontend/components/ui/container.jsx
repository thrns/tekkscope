import { cn } from '@/lib/utils';

const Container = ({
  className,
  children,
  as: Component = 'div',
  ...props
}) => {
  return (
    <Component
      className={cn('mx-auto w-full max-w-7xl px-4 md:px-8', className)}
      {...props}
    >
      {children}
    </Component>
  );
};

export { Container };
