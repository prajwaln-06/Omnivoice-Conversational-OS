export default function Card({ children, className = "", onClick }) {
  return (
    <div onClick={onClick} className={`glass p-6 ${className}`}>
      {children}
    </div>
  );
}