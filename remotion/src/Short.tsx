import React from 'react';
import {
  AbsoluteFill, Audio, OffthreadVideo, Img, Sequence, interpolate, spring, staticFile,
  useCurrentFrame, useVideoConfig, Easing,
} from 'remotion';

type Word = {w: string; s: number; e: number};
type Scene = {
  headline: string; sub: string; emoji: string; accent: string; count?: number;
  keywords: string[]; text: string; start: number; dur: number; words: Word[];
  media?: string; mediaType?: 'video' | 'image';
};
export type ShortProps = {title: string; total: number; scenes: Scene[]; music?: string};

const FONT = "'Inter Display', 'Inter', sans-serif";
const clean = (w: string) => w.toLowerCase().replace(/[^a-z0-9']/g, '');

const Grain: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{opacity: 0.09, mixBlendMode: 'overlay'}}>
      <svg width="1080" height="1920">
        <filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={f % 12} /></filter>
        <rect width="100%" height="100%" filter="url(#n)" />
      </svg>
    </AbsoluteFill>
  );
};

const Background: React.FC<{scene: Scene; local: number}> = ({scene, local}) => {
  const {fps} = useVideoConfig();
  const t = local / fps;
  const zoom = interpolate(local, [0, scene.dur * fps], [1.12, 1.0]);
  const a = scene.accent;
  return (
    <AbsoluteFill style={{background: '#0b0618', overflow: 'hidden'}}>
      {scene.media ? (
        <AbsoluteFill style={{transform: `scale(${zoom}) translateY(${Math.sin(t) * 8}px)`}}>
          {scene.mediaType === 'image'
            ? <Img src={staticFile(scene.media)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
            : <OffthreadVideo muted src={staticFile(scene.media)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />}
        </AbsoluteFill>
      ) : (
        <AbsoluteFill>
          {[0, 1, 2].map((i) => (
            <div key={i} style={{
              position: 'absolute', width: 1300, height: 1300, borderRadius: '50%',
              left: -300 + 500 * Math.sin(t * 0.5 + i * 2.1) + i * 150,
              top: -200 + i * 650 + 220 * Math.cos(t * 0.4 + i),
              background: `radial-gradient(circle, ${i === 1 ? '#ffffff55' : a} 0%, transparent 65%)`,
              opacity: i === 1 ? 0.6 : 1, filter: 'blur(30px)',
            }} />
          ))}
        </AbsoluteFill>
      )}
      {/* colour grade + readability */}
      <AbsoluteFill style={{background: `linear-gradient(180deg, ${a}55 0%, #0b061899 45%, #0b0618ee 100%)`, mixBlendMode: 'normal'}} />
      <AbsoluteFill style={{background: `radial-gradient(ellipse at 50% 40%, transparent 40%, #000000aa 100%)`}} />
    </AbsoluteFill>
  );
};

const Headline: React.FC<{scene: Scene; local: number}> = ({scene, local}) => {
  const {fps} = useVideoConfig();
  let text = scene.headline;
  if (scene.count !== undefined) {
    const p = interpolate(local, [0, 18], [0, 1], {extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
    const from = scene.count > 100 ? scene.count - 60 : 0;
    const n = Math.round(from + (scene.count - from) * p);
    text = scene.headline.replace(String(scene.count), String(n));
  }
  const letters = text.split('');
  const size = Math.min(230, 1450 / Math.max(4, text.length));
  const subIn = spring({frame: local - 10, fps, config: {damping: 14}});
  return (
    <div style={{position: 'absolute', top: 300, width: '100%', textAlign: 'center'}}>
      <div style={{fontFamily: FONT, fontWeight: 900, fontSize: size, color: 'white', letterSpacing: -4,
        lineHeight: 1, whiteSpace: 'nowrap'}}>
        {letters.map((ch, i) => {
          const s = spring({frame: local - i * 1.5, fps, config: {damping: 11, stiffness: 160}});
          return (
            <span key={i} style={{display: 'inline-block', transform: `translateY(${(1 - s) * 120}px) scale(${0.4 + 0.6 * s}) rotate(${(1 - s) * (i % 2 ? 12 : -12)}deg)`,
              opacity: Math.min(1, s * 1.5), textShadow: `0 8px 0 ${scene.accent}, 0 18px 40px #000a`,
              WebkitTextStroke: '6px #120a24', paintOrder: 'stroke fill'}}>
              {ch === ' ' ? ' ' : ch}
            </span>
          );
        })}
      </div>
      <div style={{marginTop: 34, display: 'inline-block', transform: `scale(${subIn}) rotate(-2deg)`,
        background: scene.accent, color: '#120a24', fontFamily: FONT, fontWeight: 900, fontSize: 50,
        padding: '12px 30px', borderRadius: 18, textTransform: 'uppercase', boxShadow: '0 12px 30px #0008'}}>
        {scene.sub}
      </div>
    </div>
  );
};

const Hero: React.FC<{scene: Scene; local: number}> = ({scene, local}) => {
  const {fps} = useVideoConfig();
  const s = spring({frame: local - 6, fps, config: {damping: 9, stiffness: 120}});
  const t = local / fps;
  const ring = interpolate((local % 45) / 45, [0, 1], [0.6, 1.5]);
  return (
    <div style={{position: 'absolute', top: 760, left: 0, width: '100%', height: 420, display: 'flex',
      justifyContent: 'center', alignItems: 'center'}}>
      <div style={{position: 'absolute', width: 380, height: 380, borderRadius: '50%',
        border: `10px solid ${scene.accent}`, transform: `scale(${ring})`, opacity: 1.5 - ring}} />
      <div style={{position: 'absolute', width: 330, height: 330, borderRadius: '50%',
        background: `radial-gradient(circle, ${scene.accent}aa, transparent 70%)`, transform: `scale(${s})`}} />
      <div style={{fontSize: 260, transform: `scale(${s}) rotate(${Math.sin(t * 3) * 8}deg) translateY(${Math.sin(t * 2.4) * 14}px)`,
        filter: 'drop-shadow(0 20px 30px #0009)'}}>{scene.emoji}</div>
    </div>
  );
};

const Captions: React.FC<{scene: Scene; time: number}> = ({scene, time}) => {
  const {fps} = useVideoConfig();
  const groups: Word[][] = [];
  scene.words.forEach((w, i) => {
    const g = groups[groups.length - 1];
    const brk = !g || g.length >= 3 || /[.,?!:]$/.test(g[g.length - 1].w) && g.length >= 1 && i > 0;
    if (brk) groups.push([w]); else g.push(w);
  });
  const g = groups.find((gr, i) => time >= gr[0].s - 0.05 && time < (groups[i + 1]?.[0].s ?? scene.start + scene.dur));
  if (!g) return null;
  const kw = new Set(scene.keywords.map(clean));
  return (
    <div style={{position: 'absolute', top: 1250, width: '100%', display: 'flex', justifyContent: 'center',
      flexWrap: 'wrap', gap: 18, padding: '0 70px', boxSizing: 'border-box'}}>
      {g.map((w, i) => {
        const nextS = g[i + 1]?.s ?? w.e + 0.25;
        const active = time >= w.s && time < nextS;
        const pop = spring({frame: Math.round((time - w.s) * fps), fps, config: {damping: 10, stiffness: 220}});
        const isKw = kw.has(clean(w.w));
        return (
          <span key={i} style={{fontFamily: FONT, fontWeight: 900, fontSize: 96, lineHeight: 1.15,
            textTransform: 'uppercase', color: active ? '#120a24' : isKw ? scene.accent : 'white',
            background: active ? scene.accent : 'transparent', borderRadius: 16, padding: '0 14px',
            transform: `scale(${time >= w.s ? 0.85 + 0.15 * pop + (active ? 0.06 : 0) : 0.85}) rotate(${active ? -2 : 0}deg)`,
            opacity: time >= w.s - 0.05 ? 1 : 0.35,
            WebkitTextStroke: active ? '0px' : '5px #120a24', paintOrder: 'stroke fill',
            textShadow: active ? 'none' : '0 6px 18px #000c'}}>
            {w.w}
          </span>
        );
      })}
    </div>
  );
};

const Transition: React.FC<{local: number}> = ({local}) => {
  const flash = interpolate(local, [0, 6], [0.85, 0], {extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{background: 'white', opacity: flash, pointerEvents: 'none'}} />;
};

export const Short: React.FC<ShortProps> = ({scenes, total, music}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const time = frame / fps;
  const idx = Math.max(0, scenes.findIndex((s, i) => time >= s.start && (i === scenes.length - 1 || time < scenes[i + 1].start)));
  const scene = scenes[idx];
  if (!scene) return null;
  const local = frame - Math.round(scene.start * fps);
  const punch = interpolate(local, [0, 8], [1.18, 1], {extrapolateRight: 'clamp', easing: Easing.out(Easing.exp)});
  const blur = interpolate(local, [0, 6], [14, 0], {extrapolateRight: 'clamp'});
  const shake = local < 8 ? Math.sin(local * 2.3) * (8 - local) * 2 : 0;
  return (
    <AbsoluteFill style={{background: '#0b0618'}}>
      <AbsoluteFill style={{transform: `scale(${punch}) translate(${shake}px, ${-shake / 2}px)`, filter: `blur(${blur}px)`}}>
        <Background scene={scene} local={local} />
        <Hero scene={scene} local={local} />
        <Headline scene={scene} local={local} />
      </AbsoluteFill>
      <Captions scene={scene} time={time} />
      <Grain />
      <Transition local={local} />
      {/* progress bar */}
      <div style={{position: 'absolute', top: 110, left: 60, right: 60, height: 14, borderRadius: 8, background: '#ffffff33'}}>
        <div style={{width: `${(time / total) * 100}%`, height: '100%', borderRadius: 8, background: scene.accent,
          boxShadow: `0 0 20px ${scene.accent}`}} />
      </div>
      <div style={{position: 'absolute', top: 1560, width: '100%', textAlign: 'center', fontFamily: FONT,
        fontWeight: 800, fontSize: 34, color: '#ffffffcc', letterSpacing: 6}}>WHAT · WHY · HOW</div>
      <Audio src={staticFile('voice.wav')} volume={1} />
      {music && <Audio src={staticFile(music)} volume={0.14} />}
      {scenes.map((s, i) => (
        <Sequence key={i} from={Math.max(0, Math.round(s.start * fps) - 3)} durationInFrames={30}>
          <Audio src={staticFile('whoosh.wav')} volume={0.5} />
        </Sequence>
      ))}
      {scenes.map((s, i) => (
        <Sequence key={'p' + i} from={Math.round(s.start * fps) + 8} durationInFrames={15}>
          <Audio src={staticFile('pop.wav')} volume={0.45} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
