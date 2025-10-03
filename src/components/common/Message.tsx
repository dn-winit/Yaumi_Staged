import React from 'react';

interface MessageProps {
  type: 'success' | 'info' | 'error';
  icon: React.ReactNode;
  children: React.ReactNode;
}

const Message: React.FC<MessageProps> = ({ type, icon, children }) => {
  const className = type === 'success'
    ? 'ui-message-success'
    : type === 'info'
    ? 'ui-message-info'
    : 'ui-message-error';

  return (
    <div className={className}>
      <span className="ui-icon-sm mr-1.5">{icon}</span>
      {children}
    </div>
  );
};

export default Message;
