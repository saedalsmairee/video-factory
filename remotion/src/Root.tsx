import React from 'react';
import {Composition} from 'remotion';
import {Short, ShortProps} from './Short';

const FPS = 30;
export const Root: React.FC = () => (
  <Composition
    id="Short"
    component={Short as any}
    width={1080}
    height={1920}
    fps={FPS}
    durationInFrames={300}
    defaultProps={{total: 10, scenes: [], title: ''} as ShortProps}
    calculateMetadata={({props}) => ({durationInFrames: Math.ceil(((props as ShortProps).total + 0.6) * FPS)})}
  />
);
