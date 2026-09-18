import { useEffect, useRef, useState } from "react"

interface AnimatedAcanthusEyeProps {
  className?: string
}

export function AnimatedAcanthusEye({ className = "" }: AnimatedAcanthusEyeProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)
  const [parallax, setParallax] = useState({ x: 0, y: 0 })
  const [isLoaded, setIsLoaded] = useState(false)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    // Try WebGL context
    const gl = (canvas.getContext("webgl", {
      alpha: true,
      premultipliedAlpha: false,
    }) ||
      canvas.getContext("experimental-webgl", {
        alpha: true,
        premultipliedAlpha: false,
      })) as WebGLRenderingContext | null

    if (!gl) {
      console.warn("WebGL not available, falling back to static image")
      return
    }

    let animationFrameId: number
    let startTime = performance.now()

    // 1. Shaders
    const vsSource = `
      attribute vec2 aPosition;
      varying vec2 vUv;
      void main() {
        vUv = (aPosition + 1.0) * 0.5;
        vUv.y = 1.0 - vUv.y; // Flip Y for WebGL texture orientation
        gl_Position = vec4(aPosition, 0.0, 1.0);
      }
    `

    const fsSource = `
      precision highp float;
      varying vec2 vUv;
      uniform sampler2D uMasterTexture;
      uniform sampler2D uPupilTexture;
      uniform float uTime;
      uniform vec2 uCenter;

      void main() {
        vec2 coord = vUv;
        vec4 baseColor = texture2D(uMasterTexture, coord);

        // Distance from pupil center in normalized UV coordinates (1024 base)
        vec2 delta = coord - uCenter;
        float r = length(delta);
        float r_px = r * 1024.0;

        // Outside pupil opening: preserve master copperplate engraving with zero distortion
        if (r_px > 82.0) {
          gl_FragColor = baseColor;
          return;
        }

        float theta = atan(delta.y, delta.x);

        // Continuous outward blooming flow: dual-phase hypnotic zoom & curl
        float speed = 0.09;
        float p1 = fract(uTime * speed);
        float p2 = fract(uTime * speed + 0.5);

        float s_base = 5.0;
        float scale_factor = 2.3;
        float s1 = s_base / pow(scale_factor, p1);
        float s2 = s_base / pow(scale_factor, p2);

        float rot1 = -0.38 * p1 - uTime * 0.05;
        float rot2 = -0.38 * p2 - uTime * 0.05;

        // Normalized distance in 512x512 pupil texture
        vec2 pupilCenter = vec2(0.5, 0.5);
        float r_pupil_1 = (r_px * s1) / 512.0;
        float r_pupil_2 = (r_px * s2) / 512.0;

        vec2 uv1 = pupilCenter + vec2(r_pupil_1 * cos(theta + rot1), r_pupil_1 * sin(theta + rot1));
        vec2 uv2 = pupilCenter + vec2(r_pupil_2 * cos(theta + rot2), r_pupil_2 * sin(theta + rot2));

        vec4 col1 = texture2D(uPupilTexture, uv1);
        vec4 col2 = texture2D(uPupilTexture, uv2);

        // Dual-phase bell curve crossfade
        float w1 = pow(sin(p1 * 3.14159265), 1.2);
        float w2 = pow(sin(p2 * 3.14159265), 1.2);

        // Stroke-preserving blend between dual-phase blooming layers
        float a1 = col1.a * w1;
        float a2 = col2.a * w2;
        float flowAlpha = max(a1, a2);
        flowAlpha = clamp(flowAlpha * 1.35, 0.0, 1.0);

        // Ultra-soft seamless edge fade under the surrounding acanthus leaves
        // Leaves start at ~36-40px and become fully solid by ~65-76px
        float fade = 1.0 - smoothstep(46.0, 76.0, r_px);
        fade = fade * fade * (3.0 - 2.0 * fade);
        flowAlpha *= fade;

        // Composite: static wreath leaves sit ON TOP of blooming petals
        vec4 finalColor;
        finalColor.rgb = vec3(1.0);
        finalColor.a = clamp(baseColor.a + flowAlpha * (1.0 - baseColor.a), 0.0, 1.0);

        gl_FragColor = finalColor;
      }
    `

    const createShader = (type: number, source: string) => {
      const shader = gl.createShader(type)
      if (!shader) return null
      gl.shaderSource(shader, source)
      gl.compileShader(shader)
      if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        console.error("Shader compile error:", gl.getShaderInfoLog(shader))
        gl.deleteShader(shader)
        return null
      }
      return shader
    }

    const vs = createShader(gl.VERTEX_SHADER, vsSource)
    const fs = createShader(gl.FRAGMENT_SHADER, fsSource)
    if (!vs || !fs) return

    const program = gl.createProgram()
    if (!program) return
    gl.attachShader(program, vs)
    gl.attachShader(program, fs)
    gl.linkProgram(program)
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.error("Program link error:", gl.getProgramInfoLog(program))
      return
    }

    gl.useProgram(program)

    // Full-screen quad
    const positions = new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1])
    const posBuffer = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, posBuffer)
    gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW)

    const aPosLoc = gl.getAttribLocation(program, "aPosition")
    gl.enableVertexAttribArray(aPosLoc)
    gl.vertexAttribPointer(aPosLoc, 2, gl.FLOAT, false, 0, 0)

    // Uniform locations
    const uMasterTexLoc = gl.getUniformLocation(program, "uMasterTexture")
    const uPupilTexLoc = gl.getUniformLocation(program, "uPupilTexture")
    const uTimeLoc = gl.getUniformLocation(program, "uTime")
    const uCenterLoc = gl.getUniformLocation(program, "uCenter")

    // Center in normalized UV coords (505/1024, 500/1024)
    gl.uniform2f(uCenterLoc, 505.0 / 1024.0, 500.0 / 1024.0)
    gl.uniform1i(uMasterTexLoc, 0)
    gl.uniform1i(uPupilTexLoc, 1)

    // Load master texture and pupil rosette texture
    let loadedCount = 0
    const onTextureLoaded = () => {
      loadedCount++
      if (loadedCount === 2) {
        setIsLoaded(true)
        render()
      }
    }

    const masterTexture = gl.createTexture()
    const masterImg = new Image()
    masterImg.src = "/assets/images/brand-hero-master.png"
    masterImg.crossOrigin = "anonymous"
    masterImg.onload = () => {
      gl.activeTexture(gl.TEXTURE0)
      gl.bindTexture(gl.TEXTURE_2D, masterTexture)
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR)
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR)
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, masterImg)
      onTextureLoaded()
    }

    const pupilTexture = gl.createTexture()
    const pupilImg = new Image()
    pupilImg.src = "/assets/images/acanthus-pupil-texture.png"
    pupilImg.crossOrigin = "anonymous"
    pupilImg.onload = () => {
      gl.activeTexture(gl.TEXTURE1)
      gl.bindTexture(gl.TEXTURE_2D, pupilTexture)
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR)
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR)
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, pupilImg)
      gl.generateMipmap(gl.TEXTURE_2D)
      onTextureLoaded()
    }

    const updateCanvasDPI = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      const rect = canvas.getBoundingClientRect()
      if (rect.width > 0 && rect.height > 0) {
        canvas.width = Math.round(rect.width * dpr)
        canvas.height = Math.round(rect.height * dpr)
        gl.viewport(0, 0, canvas.width, canvas.height)
      }
    }

    updateCanvasDPI()
    window.addEventListener("resize", updateCanvasDPI)

    // 60 FPS Render Loop
    const render = () => {
      const elapsed = (performance.now() - startTime) / 1000.0
      gl.uniform1f(uTimeLoc, elapsed)

      gl.activeTexture(gl.TEXTURE0)
      gl.bindTexture(gl.TEXTURE_2D, masterTexture)

      gl.activeTexture(gl.TEXTURE1)
      gl.bindTexture(gl.TEXTURE_2D, pupilTexture)

      gl.clearColor(0.0, 0.0, 0.0, 0.0)
      gl.clear(gl.COLOR_BUFFER_BIT)
      gl.drawArrays(gl.TRIANGLES, 0, 6)

      animationFrameId = requestAnimationFrame(render)
    }

    return () => {
      cancelAnimationFrame(animationFrameId)
      window.removeEventListener("resize", updateCanvasDPI)
      gl.deleteProgram(program)
      gl.deleteShader(vs)
      gl.deleteShader(fs)
      gl.deleteTexture(masterTexture)
      gl.deleteTexture(pupilTexture)
      gl.deleteBuffer(posBuffer)
    }
  }, [])

  // Interactive 2.5D Parallax Mouse Handlers
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = containerRef.current?.getBoundingClientRect()
    if (!rect) return
    const normX = ((e.clientX - rect.left) / rect.width - 0.5) * 2
    const normY = ((e.clientY - rect.top) / rect.height - 0.5) * 2
    setParallax({ x: normX * 12, y: normY * 12 })
  }

  const handleMouseLeave = () => {
    setParallax({ x: 0, y: 0 })
  }

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`relative w-full max-w-[560px] aspect-square flex items-center justify-center select-none transition-transform duration-300 ease-out ${className}`}
      style={{
        transform: `perspective(1000px) rotateX(${-parallax.y * 0.3}deg) rotateY(${parallax.x * 0.3}deg)`,
      }}
    >
      {/* 60 FPS Living Baroque Acanthus Eye WebGL Canvas */}
      <canvas
        ref={canvasRef}
        className="w-full h-full object-contain filter drop-shadow-[0_0_40px_rgba(255,255,255,0.22)] select-none"
      />

      {/* Fallback while texture is loading or if WebGL is disabled */}
      {!isLoaded && (
        <img
          src="/assets/images/brand-hero-master.png"
          alt="反詐大師 · 古典全視透鏡之眼"
          className="absolute inset-0 w-full h-full object-contain filter drop-shadow-[0_0_40px_rgba(255,255,255,0.22)] select-none pointer-events-none"
        />
      )}
    </div>
  )
}
