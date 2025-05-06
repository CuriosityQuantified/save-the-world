
import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function Home() {
  const router = useRouter();
  
  useEffect(() => {
    router.push('/simulation');
  }, []);

  return (
    <div>
      <h1>Redirecting to simulation...</h1>
    </div>
  );
}
