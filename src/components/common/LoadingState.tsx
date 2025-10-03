import React from 'react';

interface LoadingStateProps {
  title?: string;
  message?: string;
  spinnerColor?: string;
}

const LoadingState: React.FC<LoadingStateProps> = ({
  title = 'Loading Data',
  message = 'Please wait...',
  spinnerColor = 'border-blue-600'
}) => {
  return (
    <div className="ui-card">
      <div className="ui-loading-container">
        <div className={`ui-loading-spinner border-gray-200 ${spinnerColor}`}></div>
        <h3 className="ui-loading-title">{title}</h3>
        <p className="ui-loading-text">{message}</p>
      </div>
    </div>
  );
};

export default LoadingState;
