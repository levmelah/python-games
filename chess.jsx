import React, { useState, useMemo, useEffect, useRef } from "react";

// ---------- Chess logic ----------
const initialBoard = () => {
  const b = Array.from({ length: 8 }, () => Array(8).fill(null));
  const back = ["r", "n", "b", "q", "k", "b", "n", "r"];
  for (let c = 0; c < 8; c++) {
    b[0][c] = { type: back[c], color: "b" };
    b[1][c] = { type: "p", color: "b" };
    b[6][c] = { type: "p", color: "w" };
    b[7][c] = { type: back[c], color: "w" };
  }
  return b;
};

const inBounds = (r, c) => r >= 0 && r < 8 && c >= 0 && c < 8;
const opposite = (color) => (color === "w" ? "b" : "w");

function pseudoMoves(board, r, c, enPassant) {
  const piece = board[r][c];
  if (!piece) return [];
  const { type, color } = piece;
  const moves = [];
  const dir = color === "w" ? -1 : 1;

  const addSlide = (dirs) => {
    for (const [dr, dc] of dirs) {
      let nr = r + dr,
        nc = c + dc;
      while (inBounds(nr, nc)) {
        const target = board[nr][nc];
        if (!target) {
          moves.push([nr, nc]);
        } else {
          if (target.color !== color) moves.push([nr, nc]);
          break;
        }
        nr += dr;
        nc += dc;
      }
    }
  };

  if (type === "p") {
    if (inBounds(r + dir, c) && !board[r + dir][c]) {
      moves.push([r + dir, c]);
      const startRow = color === "w" ? 6 : 1;
      if (r === startRow && !board[r + 2 * dir][c]) {
        moves.push([r + 2 * dir, c]);
      }
    }
    for (const dc of [-1, 1]) {
      const nr = r + dir,
        nc = c + dc;
      if (inBounds(nr, nc)) {
        const target = board[nr][nc];
        if (target && target.color !== color) moves.push([nr, nc]);
        else if (
          enPassant &&
          enPassant[0] === nr &&
          enPassant[1] === nc &&
          !target
        ) {
          moves.push([nr, nc, "ep"]);
        }
      }
    }
  } else if (type === "n") {
    const deltas = [
      [-2, -1], [-2, 1], [-1, -2], [-1, 2],
      [1, -2], [1, 2], [2, -1], [2, 1],
    ];
    for (const [dr, dc] of deltas) {
      const nr = r + dr,
        nc = c + dc;
      if (inBounds(nr, nc)) {
        const target = board[nr][nc];
        if (!target || target.color !== color) moves.push([nr, nc]);
      }
    }
  } else if (type === "b") {
    addSlide([[-1, -1], [-1, 1], [1, -1], [1, 1]]);
  } else if (type === "r") {
    addSlide([[-1, 0], [1, 0], [0, -1], [0, 1]]);
  } else if (type === "q") {
    addSlide([
      [-1, -1], [-1, 1], [1, -1], [1, 1],
      [-1, 0], [1, 0], [0, -1], [0, 1],
    ]);
  } else if (type === "k") {
    for (let dr = -1; dr <= 1; dr++) {
      for (let dc = -1; dc <= 1; dc++) {
        if (dr === 0 && dc === 0) continue;
        const nr = r + dr,
          nc = c + dc;
        if (inBounds(nr, nc)) {
          const target = board[nr][nc];
          if (!target || target.color !== color) moves.push([nr, nc]);
        }
      }
    }
  }
  return moves;
}

function findKing(board, color) {
  for (let r = 0; r < 8; r++)
    for (let c = 0; c < 8; c++) {
      const p = board[r][c];
      if (p && p.type === "k" && p.color === color) return [r, c];
    }
  return null;
}

function isSquareAttacked(board, r, c, byColor, enPassant) {
  for (let rr = 0; rr < 8; rr++)
    for (let cc = 0; cc < 8; cc++) {
      const p = board[rr][cc];
      if (p && p.color === byColor) {
        const moves = pseudoMoves(board, rr, cc, enPassant);
        if (moves.some(([mr, mc]) => mr === r && mc === c)) return true;
      }
    }
  return false;
}

function applyMove(board, from, to, promo) {
  const nb = board.map((row) => row.slice());
  const piece = nb[from[0]][from[1]];
  const isEp = to[2] === "ep";
  nb[to[0]][to[1]] = piece;
  nb[from[0]][from[1]] = null;
  if (isEp) {
    nb[from[0]][to[1]] = null;
  }
  if (piece.type === "p" && (to[0] === 0 || to[0] === 7)) {
    nb[to[0]][to[1]] = { type: promo || "q", color: piece.color };
  }
  return nb;
}

function legalMoves(board, r, c, enPassant) {
  const piece = board[r][c];
  if (!piece) return [];
  const moves = pseudoMoves(board, r, c, enPassant);
  return moves.filter((m) => {
    const nb = applyMove(board, [r, c], m);
    const kingPos = findKing(nb, piece.color);
    if (!kingPos) return false;
    return !isSquareAttacked(nb, kingPos[0], kingPos[1], opposite(piece.color), null);
  });
}

function allLegalMoves(board, color, enPassant) {
  const all = [];
  for (let r = 0; r < 8; r++)
    for (let c = 0; c < 8; c++) {
      const p = board[r][c];
      if (p && p.color === color) {
        const ms = legalMoves(board, r, c, enPassant);
        ms.forEach((m) => all.push({ from: [r, c], to: m }));
      }
    }
  return all;
}

const PIECE_UNICODE = {
  w: { k: "♔", q: "♕", r: "♖", b: "♗", n: "♘", p: "♙" },
  b: { k: "♚", q: "♛", r: "♜", b: "♝", n: "♞", p: "♟" },
};

const SQ = 52; // square size in px

// Unicode white-piece glyphs are hollow outlines by design, so plain CSS
// color leaves the interior see-through. To render a solid white piece we
// layer the solid black-shaped glyph (colored white) underneath the
// outline glyph (colored dark) so it reads as a filled white piece with a
// crisp dark outline, on any square color.
function PieceGlyph({ color, type, size = 34 }) {
  if (color === "b") {
    return (
      <span style={{ display: "inline-block", fontSize: size, lineHeight: 1, color: "#1a1512" }}>
        {PIECE_UNICODE.b[type]}
      </span>
    );
  }
  return (
    <span style={{ position: "relative", display: "inline-block", fontSize: size, lineHeight: 1 }}>
      <span aria-hidden="true" style={{ position: "absolute", top: 0, left: 0, color: "#fdfaf4" }}>
        {PIECE_UNICODE.b[type]}
      </span>
      <span style={{ position: "relative", color: "#241a13" }}>{PIECE_UNICODE.w[type]}</span>
    </span>
  );
}

// A ring of small teeth around a pit/mouth-shaped circle, pointing inward.
function PitTeeth({ radius = 20, count = 10, size = 7 }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => {
        const angle = (360 / count) * i;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              top: "50%",
              left: "50%",
              width: 0,
              height: 0,
              transform: `translate(-50%, -50%) rotate(${angle}deg) translateY(-${radius}px)`,
            }}
          >
            <div
              style={{
                width: 0,
                height: 0,
                borderLeft: `${size * 0.6}px solid transparent`,
                borderRight: `${size * 0.6}px solid transparent`,
                borderTop: `${size}px solid #f2ece0`,
                transform: "translateX(-50%)",
                filter: "drop-shadow(0 1px 1px rgba(0,0,0,0.5))",
              }}
            />
          </div>
        );
      })}
    </>
  );
}

// A captured piece's afterlife: standing on a little cloud, with wings and
// a halo, regardless of which side it belonged to.
function AngelPiece({ color, type }) {
  return (
    <div
      style={{
        position: "relative",
        width: "34px",
        height: "42px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-end",
        flexShrink: 0,
      }}
    >
      <div
        style={{
          position: "absolute",
          top: "-2px",
          left: "50%",
          transform: "translateX(-50%)",
          width: "13px",
          height: "13px",
          borderRadius: "50%",
          border: "2.5px solid #f4d35e",
          boxShadow: "0 0 5px 1px rgba(244,211,94,0.75)",
          zIndex: 3,
        }}
      />
      <div
        style={{
          position: "absolute",
          top: "13px",
          left: "-4px",
          width: "13px",
          height: "19px",
          background: "linear-gradient(135deg, #ffffff, #e7e2d6)",
          borderRadius: "70% 30% 70% 30% / 60% 40% 60% 40%",
          transform: "rotate(-25deg)",
          boxShadow: "0 0 2px rgba(0,0,0,0.2)",
          zIndex: 1,
        }}
      />
      <div
        style={{
          position: "absolute",
          top: "13px",
          right: "-4px",
          width: "13px",
          height: "19px",
          background: "linear-gradient(225deg, #ffffff, #e7e2d6)",
          borderRadius: "30% 70% 30% 70% / 40% 60% 40% 60%",
          transform: "rotate(25deg)",
          boxShadow: "0 0 2px rgba(0,0,0,0.2)",
          zIndex: 1,
        }}
      />
      <div style={{ position: "relative", zIndex: 2, marginBottom: "5px" }}>
        <PieceGlyph color={color} type={type} size={20} />
      </div>
      <div
        style={{
          position: "absolute",
          bottom: "0",
          left: "50%",
          transform: "translateX(-50%)",
          width: "28px",
          height: "9px",
          background: "#ffffff",
          borderRadius: "50%",
          boxShadow: "-6px 2px 0 -1px #ffffff, 6px 2px 0 -1px #ffffff, 0 3px 0 -1.5px #ffffff",
          zIndex: 2,
        }}
      />
    </div>
  );
}

export default function ChessGame() {
  const [board, setBoard] = useState(initialBoard);
  const [turn, setTurn] = useState("w");
  const [selected, setSelected] = useState(null);
  const [enPassant, setEnPassant] = useState(null);
  const [captured, setCaptured] = useState({ w: [], b: [] });

  const [anim, setAnim] = useState(null);
  const timeoutRef = useRef(null);

  const moves = useMemo(() => {
    if (!selected || anim) return [];
    return legalMoves(board, selected[0], selected[1], enPassant);
  }, [board, selected, enPassant, anim]);

  const allMoves = useMemo(() => allLegalMoves(board, turn, enPassant), [board, turn, enPassant]);
  const kingPos = useMemo(() => findKing(board, turn), [board, turn]);
  const inCheck = useMemo(
    () => kingPos && isSquareAttacked(board, kingPos[0], kingPos[1], opposite(turn), enPassant),
    [board, kingPos, turn, enPassant]
  );
  const gameOver = allMoves.length === 0;
  const status = gameOver
    ? inCheck
      ? `שח מט! ${turn === "w" ? "שחור" : "לבן"} מנצח`
      : "תיקו (פאט)"
    : inCheck
    ? `${turn === "w" ? "לבן" : "שחור"} בשח!`
    : `תור ${turn === "w" ? "הלבן" : "השחור"}`;

  useEffect(() => {
    if (anim && anim.phase === "slide") {
      const id = requestAnimationFrame(() => {
        setAnim((a) => (a ? { ...a, phase: "arrived" } : a));
      });
      return () => cancelAnimationFrame(id);
    }
    if (anim && anim.phase === "arrived") {
      timeoutRef.current = setTimeout(() => {
        setAnim((a) => (a ? { ...a, phase: a.capturedPiece ? "clash" : "done" } : a));
      }, 280);
      return () => clearTimeout(timeoutRef.current);
    }
    if (anim && anim.phase === "clash") {
      timeoutRef.current = setTimeout(() => {
        setAnim((a) => (a ? { ...a, phase: "kill" } : a));
      }, 260);
      return () => clearTimeout(timeoutRef.current);
    }
    if (anim && anim.phase === "aim") {
      timeoutRef.current = setTimeout(() => {
        setAnim((a) => (a ? { ...a, phase: "shoot" } : a));
      }, 300);
      return () => clearTimeout(timeoutRef.current);
    }
    if (anim && anim.phase === "shoot") {
      timeoutRef.current = setTimeout(() => {
        setAnim((a) => (a ? { ...a, phase: "kill" } : a));
      }, 240);
      return () => clearTimeout(timeoutRef.current);
    }
    if (anim && anim.phase === "lever") {
      timeoutRef.current = setTimeout(() => {
        setAnim((a) => (a ? { ...a, phase: "trapdoorOpen" } : a));
      }, 500);
      return () => clearTimeout(timeoutRef.current);
    }
    if (anim && anim.phase === "trapdoorOpen") {
      timeoutRef.current = setTimeout(() => {
        setAnim((a) => (a ? { ...a, phase: "pitEmpty" } : a));
      }, 450);
      return () => clearTimeout(timeoutRef.current);
    }
    if (anim && anim.phase === "pitEmpty") {
      timeoutRef.current = setTimeout(() => {
        setAnim((a) => (a ? { ...a, phase: "trapdoorClose" } : a));
      }, 600);
      return () => clearTimeout(timeoutRef.current);
    }
    if (anim && anim.phase === "trapdoorClose") {
      timeoutRef.current = setTimeout(() => {
        setAnim((a) => (a ? { ...a, phase: "moveIn" } : a));
      }, 350);
      return () => clearTimeout(timeoutRef.current);
    }
    if (anim && anim.phase === "kill") {
      timeoutRef.current = setTimeout(() => {
        setAnim((a) => (a ? { ...a, phase: "linger" } : a));
      }, 400);
      return () => clearTimeout(timeoutRef.current);
    }
    if (anim && anim.phase === "linger") {
      timeoutRef.current = setTimeout(() => {
        setAnim((a) => (a ? { ...a, phase: "fadeout" } : a));
      }, 1000);
      return () => clearTimeout(timeoutRef.current);
    }
    if (anim && anim.phase === "fadeout") {
      timeoutRef.current = setTimeout(() => {
        setAnim((a) => {
          if (!a) return a;
          const needsMoveIn = (a.movingPiece.type === "r" || a.movingPiece.type === "b") && a.capturedPiece;
          return { ...a, phase: needsMoveIn ? "moveIn" : "done" };
        });
      }, 300);
      return () => clearTimeout(timeoutRef.current);
    }
    if (anim && anim.phase === "moveIn") {
      const id = requestAnimationFrame(() => {
        setAnim((a) => (a ? { ...a, phase: "moveInArrived" } : a));
      });
      return () => cancelAnimationFrame(id);
    }
    if (anim && anim.phase === "moveInArrived") {
      timeoutRef.current = setTimeout(() => {
        setAnim((a) => (a ? { ...a, phase: "done" } : a));
      }, 280);
      return () => clearTimeout(timeoutRef.current);
    }
    if (anim && anim.phase === "done") {
      setBoard(anim.finalBoard);
      setTurn(anim.finalTurn);
      setEnPassant(anim.finalEnPassant);
      if (anim.capturedPiece) {
        setCaptured((cap) => ({
          ...cap,
          [anim.movingPiece.color]: [...cap[anim.movingPiece.color], anim.capturedPiece.type],
        }));
      }
      setAnim(null);
    }
  }, [anim]);

  const handleSquareClick = (r, c) => {
    if (gameOver || anim) return;
    const piece = board[r][c];
    if (selected) {
      const move = moves.find((m) => m[0] === r && m[1] === c);
      if (move) {
        const movingPiece = board[selected[0]][selected[1]];
        const isEp = move[2] === "ep";
        const capturedPiece = board[r][c] || (isEp ? { type: "p", color: opposite(turn) } : null);
        const capturedAt = isEp ? [selected[0], c] : [r, c];
        const finalBoard = applyMove(board, selected, move);
        let finalEnPassant = null;
        if (movingPiece.type === "p" && Math.abs(r - selected[0]) === 2) {
          finalEnPassant = [(r + selected[0]) / 2, c];
        }
        setAnim({
          movingPiece,
          from: selected,
          to: [r, c],
          capturedPiece,
          capturedAt,
          finalBoard,
          finalTurn: opposite(turn),
          finalEnPassant,
          phase:
            movingPiece.type === "r" && capturedPiece
              ? "aim"
              : movingPiece.type === "b" && capturedPiece
              ? "lever"
              : "slide",
        });
        setSelected(null);
        return;
      }
      if (piece && piece.color === turn) {
        setSelected([r, c]);
      } else {
        setSelected(null);
      }
    } else if (piece && piece.color === turn) {
      setSelected([r, c]);
    }
  };

  const reset = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setAnim(null);
    setBoard(initialBoard());
    setTurn("w");
    setSelected(null);
    setEnPassant(null);
    setCaptured({ w: [], b: [] });
  };

  const hiddenFrom = anim ? anim.from : null;
  const hiddenCapturedAt = anim && anim.capturedPiece ? anim.capturedAt : null;
  const isQueenAttack = anim && anim.movingPiece.type === "q";
  const isKnightAttack = anim && anim.movingPiece.type === "n";
  const isRookAttack = anim && anim.movingPiece.type === "r" && !!anim.capturedPiece;
  const isBishopAttack = anim && anim.movingPiece.type === "b" && !!anim.capturedPiece;
  const isKingAttack = anim && anim.movingPiece.type === "k" && !!anim.capturedPiece;
  const atDestination = anim
    ? isRookAttack || isBishopAttack
      ? anim.phase === "moveInArrived" || anim.phase === "done"
      : anim.phase !== "slide"
    : false;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "12px",
        fontFamily: "Georgia, serif",
        background: "#2b2320",
        padding: "24px",
        borderRadius: "16px",
        color: "#f2e9dc",
        direction: "rtl",
        width: "fit-content",
      }}
    >
      <style>{`
        @keyframes killShake {
          0% { transform: translate(0,0) rotate(0deg) scale(1); }
          20% { transform: translate(-3px,-2px) rotate(-8deg) scale(1); }
          40% { transform: translate(3px,2px) rotate(8deg) scale(1); }
          60% { transform: translate(-2px,1px) rotate(-4deg) scale(0.9); }
          100% { transform: translate(0,10px) rotate(25deg) scale(0.15); opacity: 0; }
        }
        @keyframes impactFlash {
          0% { opacity: 0; transform: rotate(-40deg) scale(0.3); }
          30% { opacity: 1; transform: rotate(-40deg) scale(1.3); }
          100% { opacity: 0; transform: rotate(-40deg) scale(1.8); }
        }
        @keyframes swordA {
          0% { transform: translate(-16px,-14px) rotate(-70deg) scale(0.4); opacity: 0; }
          35% { transform: translate(-4px,-2px) rotate(-35deg) scale(1.05); opacity: 1; }
          55% { transform: translate(2px,2px) rotate(-42deg) scale(1); opacity: 1; }
          100% { transform: translate(-4px,-2px) rotate(-35deg) scale(1); opacity: 0; }
        }
        @keyframes swordB {
          0% { transform: translate(16px,-14px) rotate(70deg) scale(0.4); opacity: 0; }
          35% { transform: translate(4px,-2px) rotate(35deg) scale(1.05); opacity: 1; }
          55% { transform: translate(-2px,2px) rotate(42deg) scale(1); opacity: 1; }
          100% { transform: translate(4px,-2px) rotate(35deg) scale(1); opacity: 0; }
        }
        @keyframes slashLine {
          0% { transform: translate(-50%,-50%) rotate(-40deg) scaleX(0); opacity: 0; }
          40% { transform: translate(-50%,-50%) rotate(-40deg) scaleX(1); opacity: 1; }
          70% { opacity: 1; }
          100% { transform: translate(-50%,-50%) rotate(-40deg) scaleX(1.15); opacity: 0; }
        }
        @keyframes swingHit {
          0% { transform: rotate(0deg); }
          40% { transform: rotate(-18deg); }
          70% { transform: rotate(10deg); }
          100% { transform: rotate(0deg); }
        }
        @keyframes mouthOpen {
          0% { transform: scale(0.4); opacity: 0; }
          50% { transform: scale(1.25); opacity: 1; }
          100% { transform: scale(1); opacity: 1; }
        }
        @keyframes chompJaw {
          0% { transform: scale(1); }
          40% { transform: scale(1.35); }
          70% { transform: scale(0.95); }
          100% { transform: scale(1); }
        }
        @keyframes chewWobble {
          0% { transform: rotate(0deg) scale(1); }
          15% { transform: rotate(-6deg) scale(0.97); }
          30% { transform: rotate(4deg) scale(0.94); }
          45% { transform: rotate(-3deg) scale(0.92); }
          60% { transform: rotate(2deg) scale(0.9); }
          100% { transform: rotate(0deg) scale(0.88); }
        }
        @keyframes jawUpper {
          0% { transform: translateY(-28px); opacity: 0; }
          30% { transform: translateY(-20px); opacity: 1; }
          100% { transform: translateY(-3px); opacity: 1; }
        }
        @keyframes jawLower {
          0% { transform: translateY(28px); opacity: 0; }
          30% { transform: translateY(20px); opacity: 1; }
          100% { transform: translateY(3px); opacity: 1; }
        }
        @keyframes mouthCavity {
          0% { opacity: 0; transform: scale(0.6); }
          40% { opacity: 0.95; transform: scale(1); }
          100% { opacity: 0.3; transform: scale(0.9); }
        }
        .jaw-upper { animation: jawUpper 0.28s cubic-bezier(.3,.1,.4,1) forwards; }
        .jaw-lower { animation: jawLower 0.28s cubic-bezier(.3,.1,.4,1) forwards; }
        .mouth-cavity { animation: mouthCavity 0.28s ease-out forwards; }
        .mouth-open { animation: mouthOpen 0.26s ease-out forwards; }
        .chess-chomp { animation: chompJaw 0.26s ease-in-out; }
        .chew-wobble { animation: chewWobble 1.4s ease-out forwards; }
        @keyframes knightJump {
          0% { transform: translateY(0) scale(1); }
          35% { transform: translateY(-18px) scale(1.05,0.95); }
          55% { transform: translateY(-18px) scale(1.05,0.95); }
          80% { transform: translateY(3px) scale(1.1,0.85); }
          100% { transform: translateY(0) scale(1); }
        }
        .chess-jump { animation: knightJump 0.32s ease-in-out; }
        @keyframes squashFlat {
          0% { transform: scaleX(1) scaleY(1) translateY(0); }
          60% { transform: scaleX(1.55) scaleY(0.12) translateY(11px); }
          100% { transform: scaleX(1.4) scaleY(0.15) translateY(9px); }
        }
        .squash-flat { animation: squashFlat 0.22s ease-out forwards; }
        @keyframes splatShadow {
          0% { opacity: 0; transform: scaleX(0.4) scaleY(0.3); }
          100% { opacity: 0.5; transform: scaleX(1.2) scaleY(1); }
        }
        .splat-shadow { animation: splatShadow 0.22s ease-out forwards; }
        @keyframes gunPopIn {
          0% { transform: scale(0.3) rotate(calc(var(--gun-angle) - 15deg)); opacity: 0; }
          60% { transform: scale(1.15) rotate(calc(var(--gun-angle) + 5deg)); opacity: 1; }
          100% { transform: scale(1) rotate(var(--gun-angle)); opacity: 1; }
        }
        .gun-pop { animation: gunPopIn 0.3s ease-out forwards; }
        @keyframes muzzleFlash {
          0% { opacity: 0; transform: scale(0.3); }
          25% { opacity: 1; transform: scale(1.3); }
          100% { opacity: 0; transform: scale(0.8); }
        }
        .muzzle-flash { animation: muzzleFlash 0.18s ease-out forwards; }
        @keyframes bulletTravel {
          0% { transform: rotate(var(--bullet-angle)) scaleX(0); opacity: 1; }
          70% { transform: rotate(var(--bullet-angle)) scaleX(1); opacity: 1; }
          100% { transform: rotate(var(--bullet-angle)) scaleX(1); opacity: 0; }
        }
        .bullet-travel { animation: bulletTravel 0.2s ease-out forwards; }
        @keyframes bulletImpact {
          0% { opacity: 0; transform: scale(0.3) rotate(0deg); }
          35% { opacity: 1; transform: scale(1.4) rotate(15deg); }
          100% { opacity: 0; transform: scale(1.8) rotate(15deg); }
        }
        .bullet-impact { animation: bulletImpact 0.24s ease-out forwards; }
        @keyframes shotStagger {
          0% { transform: translate(0,0) rotate(0deg); }
          30% { transform: translate(4px,-2px) rotate(8deg); }
          60% { transform: translate(-3px,1px) rotate(-6deg); }
          100% { transform: translate(0,10px) rotate(78deg); }
        }
        .shot-stagger { animation: shotStagger 0.4s ease-in forwards; }
        @keyframes leverPress {
          0% { transform: scale(0.3); opacity: 0; }
          40% { transform: scale(1.2); opacity: 1; }
          60% { transform: scale(1); opacity: 1; }
          85% { transform: scale(0.78); opacity: 1; }
          100% { transform: scale(0.85); opacity: 1; }
        }
        .lever-press { animation: leverPress 0.5s ease-out forwards; }
        @keyframes fallInHole {
          0% { transform: translateY(0) scale(1); opacity: 1; }
          100% { transform: translateY(16px) scale(0.15); opacity: 0; }
        }
        .fall-in-hole { animation: fallInHole 0.42s ease-in forwards; }
        @keyframes kickLunge {
          0% { transform: translate(0,0) rotate(0deg); }
          35% { transform: translate(6px,-4px) rotate(-10deg); }
          55% { transform: translate(11px,-2px) rotate(-18deg); }
          100% { transform: translate(0,0) rotate(0deg); }
        }
        .chess-kick { animation: kickLunge 0.3s ease-in-out; }
        @keyframes kickedAway {
          0% { transform: translate(0,0) rotate(0deg) scale(1); opacity: 1; }
          30% { transform: translate(calc(var(--kick-dx) * 0.35), calc(var(--kick-dy) * 0.35 - 12px)) rotate(140deg) scale(0.9); opacity: 1; }
          100% { transform: translate(var(--kick-dx), calc(var(--kick-dy) - 22px)) rotate(430deg) scale(0.2); opacity: 0; }
        }
        .kicked-away { animation: kickedAway 0.38s cubic-bezier(.3,.5,.5,1) forwards; }
        @keyframes sliceTop {
          0% { transform: translate(0,0) rotate(0deg); }
          100% { transform: translate(-16px,-20px) rotate(-30deg); }
        }
        @keyframes sliceBottom {
          0% { transform: translate(0,0) rotate(0deg); }
          100% { transform: translate(16px,20px) rotate(30deg); }
        }
        .chess-impact { animation: impactFlash 0.4s ease-out forwards; }
        .chess-mover { transition: top 0.28s ease-in-out, left 0.28s ease-in-out; }
        .chess-swing { animation: swingHit 0.26s ease-in-out; }
        .sword-a { animation: swordA 0.26s ease-out forwards; }
        .sword-b { animation: swordB 0.26s ease-out forwards; }
        .slash-line { animation: slashLine 0.26s ease-out forwards; }
        .slice-top { animation: sliceTop 0.4s ease-in forwards; }
        .slice-bottom { animation: sliceBottom 0.4s ease-in forwards; }
      `}</style>

      <h2 style={{ margin: 0, letterSpacing: "1px" }}>שחמט</h2>
      <div
        style={{
          fontSize: "16px",
          fontWeight: 600,
          color: gameOver ? "#e0a458" : inCheck ? "#e05a4f" : "#f2e9dc",
        }}
      >
        {status}
      </div>

      <div style={{ display: "flex", gap: "6px", fontSize: "20px", minHeight: "28px" }}>
        <span style={{ opacity: 0.8, display: "flex", gap: "6px" }}>
          {captured.b.map((t, i) => (
            <PieceGlyph key={i} color="b" type={t} size={20} />
          ))}
        </span>
      </div>

      <div
        style={{
          position: "relative",
          display: "grid",
          gridTemplateColumns: `repeat(8, ${SQ}px)`,
          gridTemplateRows: `repeat(8, ${SQ}px)`,
          border: "4px solid #1a1512",
          borderRadius: "6px",
          overflow: "hidden",
          boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
          direction: "ltr",
        }}
      >
        {board.map((row, r) =>
          row.map((piece, c) => {
            const isDark = (r + c) % 2 === 1;
            const isSelected = selected && selected[0] === r && selected[1] === c;
            const isMoveTarget = moves.some((m) => m[0] === r && m[1] === c);
            const isKingInCheck = inCheck && kingPos && kingPos[0] === r && kingPos[1] === c;
            const hideStatic =
              (hiddenFrom && hiddenFrom[0] === r && hiddenFrom[1] === c) ||
              (hiddenCapturedAt && hiddenCapturedAt[0] === r && hiddenCapturedAt[1] === c && anim.phase !== "done") ||
              (anim && anim.to[0] === r && anim.to[1] === c);
            return (
              <div
                key={`${r}-${c}`}
                onClick={() => handleSquareClick(r, c)}
                style={{
                  width: `${SQ}px`,
                  height: `${SQ}px`,
                  background: isKingInCheck
                    ? "#b23b2f"
                    : isSelected
                    ? "#7a9b5e"
                    : isDark
                    ? "#7a5c42"
                    : "#e8d3ae",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "34px",
                  cursor: piece && piece.color === turn && !anim ? "pointer" : "default",
                  position: "relative",
                  userSelect: "none",
                }}
              >
                {piece && !hideStatic && <PieceGlyph color={piece.color} type={piece.type} size={34} />}
                {isMoveTarget && !anim && (
                  <div
                    style={{
                      position: "absolute",
                      width: piece ? "48px" : "16px",
                      height: piece ? "48px" : "16px",
                      borderRadius: "50%",
                      border: piece ? "3px solid rgba(0,0,0,0.35)" : "none",
                      background: piece ? "transparent" : "rgba(0,0,0,0.3)",
                    }}
                  />
                )}
              </div>
            );
          })
        )}

        {anim &&
          anim.capturedPiece &&
          ["arrived", "clash", "aim", "shoot", "lever"].includes(anim.phase) && (
            <div
              style={{
                position: "absolute",
                top: anim.capturedAt[0] * SQ,
                left: anim.capturedAt[1] * SQ,
                width: `${SQ}px`,
                height: `${SQ}px`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                pointerEvents: "none",
                zIndex: 2,
              }}
            >
              <PieceGlyph color={anim.capturedPiece.color} type={anim.capturedPiece.type} size={34} />
            </div>
          )}

        {anim && anim.capturedPiece && ["kill", "linger", "fadeout"].includes(anim.phase) && !isQueenAttack && !isKnightAttack && !isRookAttack && !isBishopAttack && !isKingAttack && (
          <div
            style={{
              position: "absolute",
              top: anim.capturedAt[0] * SQ,
              left: anim.capturedAt[1] * SQ,
              width: `${SQ}px`,
              height: `${SQ}px`,
              pointerEvents: "none",
              zIndex: 2,
              opacity: anim.phase === "fadeout" ? 0 : 1,
              transition: "opacity 0.3s ease",
            }}
          >
            <div
              className="slice-top"
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                clipPath: "polygon(0 0, 100% 0, 0 100%)",
              }}
            >
              <PieceGlyph color={anim.capturedPiece.color} type={anim.capturedPiece.type} size={34} />
            </div>
            <div
              className="slice-bottom"
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                clipPath: "polygon(100% 0, 100% 100%, 0 100%)",
              }}
            >
              <PieceGlyph color={anim.capturedPiece.color} type={anim.capturedPiece.type} size={34} />
            </div>
            <div
              style={{
                position: "absolute",
                top: "50%",
                left: "50%",
                width: "60px",
                height: "3px",
                background: "linear-gradient(90deg, transparent, #fff8e0 40%, #fffdf6 50%, #fff8e0 60%, transparent)",
                boxShadow: "0 0 10px 3px rgba(255,250,220,0.9)",
                transform: "translate(-50%,-50%) rotate(-40deg)",
                opacity: 0.9,
              }}
            />
          </div>
        )}

        {anim && anim.capturedPiece && ["kill", "linger", "fadeout"].includes(anim.phase) && isQueenAttack && (
          <div
            style={{
              position: "absolute",
              top: anim.capturedAt[0] * SQ,
              left: anim.capturedAt[1] * SQ,
              width: `${SQ}px`,
              height: `${SQ}px`,
              pointerEvents: "none",
              zIndex: 2,
              opacity: anim.phase === "fadeout" ? 0 : 1,
              transform: anim.phase === "fadeout" ? "scale(0.15)" : "scale(1)",
              transition: "opacity 0.3s ease, transform 0.3s ease",
            }}
          >
            <div
              className="chew-wobble"
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                WebkitMaskImage:
                  "radial-gradient(circle 11px at 74% 32%, transparent 99%, black 100%)",
                maskImage:
                  "radial-gradient(circle 11px at 74% 32%, transparent 99%, black 100%)",
              }}
            >
              <PieceGlyph color={anim.capturedPiece.color} type={anim.capturedPiece.type} size={34} />
            </div>
          </div>
        )}

        {anim && anim.capturedPiece && ["kill", "linger", "fadeout"].includes(anim.phase) && isKnightAttack && (
          <div
            style={{
              position: "absolute",
              top: anim.capturedAt[0] * SQ,
              left: anim.capturedAt[1] * SQ,
              width: `${SQ}px`,
              height: `${SQ}px`,
              pointerEvents: "none",
              zIndex: 2,
              opacity: anim.phase === "fadeout" ? 0 : 1,
              transition: "opacity 0.3s ease",
            }}
          >
            <div
              className="splat-shadow"
              style={{
                position: "absolute",
                bottom: "6px",
                left: "50%",
                width: "40px",
                height: "8px",
                marginLeft: "-20px",
                borderRadius: "50%",
                background: "rgba(0,0,0,0.5)",
              }}
            />
            <div
              className="squash-flat"
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <PieceGlyph color={anim.capturedPiece.color} type={anim.capturedPiece.type} size={34} />
            </div>
          </div>
        )}

        {/* Rook: draws a gun, aimed toward the target */}
        {anim && isRookAttack && anim.phase === "aim" && (() => {
          const dx = anim.to[1] - anim.from[1];
          const dy = anim.to[0] - anim.from[0];
          const angle = (Math.atan2(dy, dx) * 180) / Math.PI;
          const offsetX = Math.sign(dx) * SQ * 0.22;
          const offsetY = Math.sign(dy) * SQ * 0.22;
          return (
            <div
              className="gun-pop"
              style={{
                position: "absolute",
                top: anim.from[0] * SQ + SQ / 2 - 9 + offsetY,
                left: anim.from[1] * SQ + SQ / 2 - 9 + offsetX,
                fontSize: "18px",
                pointerEvents: "none",
                zIndex: 6,
                "--gun-angle": `${angle + 180}deg`,
              }}
            >
              🔫
            </div>
          );
        })()}

        {/* Rook: bullet trail from the rook's square to the target square */}
        {anim && isRookAttack && anim.phase === "shoot" && (() => {
          const dx = (anim.to[1] - anim.from[1]) * SQ;
          const dy = (anim.to[0] - anim.from[0]) * SQ;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const angle = (Math.atan2(dy, dx) * 180) / Math.PI;
          return (
            <>
              <div
                className="muzzle-flash"
                style={{
                  position: "absolute",
                  top: anim.from[0] * SQ + SQ / 2 - 8,
                  left: anim.from[1] * SQ + SQ / 2 - 8,
                  width: "16px",
                  height: "16px",
                  borderRadius: "50%",
                  background: "radial-gradient(circle, #fff6cc 0%, #f4b942 60%, transparent 80%)",
                  pointerEvents: "none",
                  zIndex: 6,
                }}
              />
              <div
                className="bullet-travel"
                style={{
                  position: "absolute",
                  top: anim.from[0] * SQ + SQ / 2 - 1,
                  left: anim.from[1] * SQ + SQ / 2,
                  width: `${dist}px`,
                  height: "2px",
                  background: "linear-gradient(90deg, #fff6cc, #f4d35e)",
                  boxShadow: "0 0 5px 1px rgba(244,211,94,0.8)",
                  transformOrigin: "left center",
                  pointerEvents: "none",
                  zIndex: 6,
                  "--bullet-angle": `${angle}deg`,
                }}
              />
              <div
                className="bullet-impact"
                style={{
                  position: "absolute",
                  top: anim.to[0] * SQ + SQ / 2 - 12,
                  left: anim.to[1] * SQ + SQ / 2 - 12,
                  width: "24px",
                  height: "24px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "22px",
                  pointerEvents: "none",
                  zIndex: 6,
                }}
              >
                💥
              </div>
            </>
          );
        })()}

        {/* Rook victim: shot and staggers to the ground */}
        {anim && anim.capturedPiece && ["kill", "linger", "fadeout"].includes(anim.phase) && isRookAttack && (
          <div
            style={{
              position: "absolute",
              top: anim.capturedAt[0] * SQ,
              left: anim.capturedAt[1] * SQ,
              width: `${SQ}px`,
              height: `${SQ}px`,
              pointerEvents: "none",
              zIndex: 2,
              opacity: anim.phase === "fadeout" ? 0 : 1,
              transition: "opacity 0.3s ease",
            }}
          >
            <div
              className="shot-stagger"
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <PieceGlyph color={anim.capturedPiece.color} type={anim.capturedPiece.type} size={34} />
            </div>
          </div>
        )}

        {/* Bishop: a button appears and gets pressed */}
        {anim && isBishopAttack && anim.phase === "lever" && (
          <div
            className="lever-press"
            style={{
              position: "absolute",
              top: anim.from[0] * SQ + SQ * 0.06,
              left: anim.from[1] * SQ + SQ * 0.06,
              width: "16px",
              height: "16px",
              borderRadius: "50%",
              background: "radial-gradient(circle at 35% 30%, #e8544a, #a3241c)",
              border: "2px solid #4a1410",
              boxShadow: "0 2px 3px rgba(0,0,0,0.5)",
              pointerEvents: "none",
              zIndex: 6,
            }}
          />
        )}

        {/* King: kicks the captured piece flying off the board */}
        {anim && anim.capturedPiece && anim.phase === "kill" && isKingAttack && (() => {
          const dx = anim.to[1] - anim.from[1];
          const dy = anim.to[0] - anim.from[0];
          const kickDx = dx * 95;
          const kickDy = dy * 95;
          return (
            <div
              style={{
                position: "absolute",
                top: anim.capturedAt[0] * SQ,
                left: anim.capturedAt[1] * SQ,
                width: `${SQ}px`,
                height: `${SQ}px`,
                pointerEvents: "none",
                zIndex: 5,
              }}
            >
              <div
                className="kicked-away"
                style={{
                  position: "absolute",
                  inset: 0,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  "--kick-dx": `${kickDx}px`,
                  "--kick-dy": `${kickDy}px`,
                }}
              >
                <PieceGlyph color={anim.capturedPiece.color} type={anim.capturedPiece.type} size={34} />
              </div>
            </div>
          );
        })()}

        {/* Bishop: the target square's floor opens into a pit */}
        {anim && isBishopAttack && ["trapdoorOpen", "pitEmpty", "trapdoorClose"].includes(anim.phase) && (
          <div
            style={{
              position: "absolute",
              top: anim.capturedAt[0] * SQ,
              left: anim.capturedAt[1] * SQ,
              width: `${SQ}px`,
              height: `${SQ}px`,
              pointerEvents: "none",
              zIndex: 2,
              opacity: anim.phase === "trapdoorClose" ? 0 : 1,
              transition: "opacity 0.35s ease",
            }}
          >
            <div
              style={{
                position: "absolute",
                inset: "4px",
                borderRadius: "50%",
                background: "radial-gradient(ellipse at center, #050505 0%, #241a14 55%, transparent 78%)",
              }}
            >
              <PitTeeth radius={19} count={11} size={7} />
            </div>
            {anim.phase === "trapdoorOpen" && (
              <div
                className="fall-in-hole"
                style={{
                  position: "absolute",
                  inset: 0,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <PieceGlyph color={anim.capturedPiece.color} type={anim.capturedPiece.type} size={34} />
              </div>
            )}
          </div>
        )}

        {anim && anim.capturedPiece && anim.phase === "clash" && !isQueenAttack && !isKnightAttack && !isRookAttack && !isBishopAttack && !isKingAttack && (
          <div
            style={{
              position: "absolute",
              top: anim.to[0] * SQ,
              left: anim.to[1] * SQ,
              width: `${SQ}px`,
              height: `${SQ}px`,
              pointerEvents: "none",
              zIndex: 5,
            }}
          >
            <div
              className="slash-line"
              style={{
                position: "absolute",
                top: "50%",
                left: "50%",
                width: "70px",
                height: "4px",
                borderRadius: "2px",
                background:
                  "linear-gradient(90deg, transparent, #fff8e0 30%, #fffdf6 50%, #fff8e0 70%, transparent)",
                boxShadow: "0 0 8px 2px rgba(255,250,220,0.8)",
              }}
            />
            <div
              className="sword-a"
              style={{
                position: "absolute",
                top: "50%",
                left: "50%",
                fontSize: "26px",
                transformOrigin: "center",
              }}
            >
              🗡️
            </div>
            <div
              className="sword-b"
              style={{
                position: "absolute",
                top: "50%",
                left: "50%",
                fontSize: "26px",
                transformOrigin: "center",
                transform: "scaleX(-1)",
              }}
            >
              🗡️
            </div>
          </div>
        )}
        {anim && anim.capturedPiece && anim.phase === "kill" && !isQueenAttack && !isKnightAttack && !isRookAttack && !isBishopAttack && !isKingAttack && (
          <div
            className="chess-impact"
            style={{
              position: "absolute",
              top: anim.to[0] * SQ,
              left: anim.to[1] * SQ,
              width: `${SQ}px`,
              height: `${SQ}px`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "30px",
              pointerEvents: "none",
              zIndex: 6,
              transform: "rotate(-40deg)",
            }}
          >
            🗡️
          </div>
        )}

        {anim && (
          <div
            className={`chess-mover${
              anim.phase === "clash"
                ? isQueenAttack
                  ? " chess-chomp"
                  : isKnightAttack
                  ? " chess-jump"
                  : isKingAttack
                  ? " chess-kick"
                  : " chess-swing"
                : ""
            }`}
            style={{
              position: "absolute",
              top: atDestination ? anim.to[0] * SQ : anim.from[0] * SQ,
              left: atDestination ? anim.to[1] * SQ : anim.from[1] * SQ,
              width: `${SQ}px`,
              height: `${SQ}px`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              pointerEvents: "none",
              zIndex: 4,
            }}
          >
            <PieceGlyph color={anim.movingPiece.color} type={anim.movingPiece.type} size={34} />
            {isQueenAttack && anim.capturedPiece && anim.phase === "clash" && (
              <div
                className="mouth-open"
                style={{
                  position: "absolute",
                  top: "-10px",
                  left: "50%",
                  transform: "translateX(-50%)",
                  fontSize: "20px",
                  pointerEvents: "none",
                }}
              >
                😮
              </div>
            )}
          </div>
        )}
      </div>

      <div style={{ display: "flex", gap: "6px", fontSize: "20px", minHeight: "28px" }}>
        <span style={{ opacity: 0.8, display: "flex", gap: "6px" }}>
          {captured.w.map((t, i) => (
            <PieceGlyph key={i} color="w" type={t} size={20} />
          ))}
        </span>
      </div>

      <button
        onClick={reset}
        style={{
          marginTop: "4px",
          padding: "8px 18px",
          background: "#7a5c42",
          color: "#fdfaf4",
          border: "none",
          borderRadius: "8px",
          cursor: "pointer",
          fontSize: "14px",
          fontFamily: "inherit",
        }}
      >
        משחק חדש
      </button>
    </div>
  );
}
