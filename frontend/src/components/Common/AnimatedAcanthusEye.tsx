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
      uniform sampler2D uTexture;
      uniform float uTime;
      uniform vec2 uCenter;
      uniform float uRimRadius;

      void main() {
        vec2 coord = vUv;
        vec2 delta = coord - uCenter;
        float r = length(delta);
        float theta = atan(delta.y, delta.x);

        vec4 baseColor = texture2D(uTexture, coord);

        // Outside the magnifying glass lens rim: render crisp original artwork
        if (r > uRimRadius + 0.025) {
          gl_FragColor = baseColor;
          return;
        }

        // Inside the magnifying glass: continuous outward blooming flow
        float rMin = 0.010;
        float rMax = uRimRadius;
        float u = clamp((r - rMin) / (rMax - rMin), 0.0, 1.0);

        // Dual-phase continuous seamless outward wave
        float speed = 0.075;
        float p1 = fract(u - uTime * speed);
        float p2 = fract(u - uTime * speed + 0.5);
        float w = sin(p1 * 3.14159265);
        w = w * w;

        // Map into the rich acanthus wreath texture band (r in [0.080, 0.155])
        float wMin = 0.082;
        float wMax = 0.156;
        float rSrc1 = wMin + p1 * (wMax - wMin);
        float rSrc2 = wMin + p2 * (wMax - wMin);

        // Natural logarithmic swirl curl
        float th1 = theta + 0.38 * (1.0 - p1) + uTime * 0.035;
        float th2 = theta + 0.38 * (1.0 - p2) + uTime * 0.035;

        vec2 uv1 = uCenter + vec2(rSrc1 * cos(th1), rSrc1 * sin(th1));
        vec2 uv2 = uCenter + vec2(rSrc2 * cos(th2), rSrc2 * sin(th2));

        vec4 col1 = texture2D(uTexture, uv1);
        vec4 col2 = texture2D(uTexture, uv2);
        vec4 flowColor = mix(col2, col1, w);

        // Smooth radial blend envelope (seamless transition into outer frame)
        float envIn = smoothstep(0.006, 0.028, r);
        float envOut = 1.0 - smoothstep(uRimRadius - 0.018, uRimRadius + 0.012, r);
        float blendFactor = envIn * envOut;

        vec4 finalColor = mix(baseColor, flowColor, blendFactor);

        // Specular optical sweep arc on antique convex glass
        float sweepAngle = theta - uTime * 0.3;
        float sweepGlint = smoothstep(0.88, 0.98, sin(sweepAngle)) *
                           smoothstep(uRimRadius * 0.5, uRimRadius * 0.92, r) *
                           envOut;
        finalColor.rgb += vec3(sweepGlint * 0.3);

        // Center breathing crystal focal dot
        float coreStar = smoothstep(0.007, 0.0015, r) * (0.85 + 0.15 * sin(uTime * 1.8));
        finalColor.rgb += vec3(coreStar);

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
    const uTexLoc = gl.getUniformLocation(program, "uTexture")
    const uTimeLoc = gl.getUniformLocation(program, "uTime")
    const uCenterLoc = gl.getUniformLocation(program, "uCenter")
    const uRimRadiusLoc = gl.getUniformLocation(program, "uRimRadius")

    // Center in normalized UV coords (506/1024, 500/1024)
    gl.uniform2f(uCenterLoc, 506.0 / 1024.0, 500.0 / 1024.0)
    // Rim radius in normalized coords (160 / 1024)
    gl.uniform1f(uRimRadiusLoc, 160.0 / 1024.0)
    gl.uniform1i(uTexLoc, 0)

    // Load master artwork image texture
    const texture = gl.createTexture()
    const img = new Image()
    img.src = "/assets/images/brand-hero-master.png"
    img.crossOrigin = "anonymous"

    img.onload = () => {
      gl.bindTexture(gl.TEXTURE_2D, texture)
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR)
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR)
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img)
      setIsLoaded(true)
      render()
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
      gl.deleteTexture(texture)
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
