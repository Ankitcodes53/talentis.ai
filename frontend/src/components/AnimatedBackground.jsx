import { useEffect, useRef } from 'react'
import './AnimatedBackground.css'

const AnimatedBackground = () => {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    let animationFrameId
    let boxes = []

    // Set canvas size
    const resizeCanvas = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
      initBoxes()
    }

    // Initialize boxes
    const initBoxes = () => {
      boxes = []
      const boxSize = 60
      const cols = Math.ceil(canvas.width / boxSize) + 2
      const rows = Math.ceil(canvas.height / boxSize) + 2

      for (let i = 0; i < cols; i++) {
        for (let j = 0; j < rows; j++) {
          boxes.push({
            x: i * boxSize,
            y: j * boxSize,
            size: boxSize,
            opacity: 0.03,
            hovered: false,
            glowIntensity: 0,
            baseOpacity: Math.random() * 0.05 + 0.02,
            pulseSpeed: Math.random() * 0.02 + 0.01,
            pulsePhase: Math.random() * Math.PI * 2,
          })
        }
      }
    }

    // Draw boxes
    const drawBoxes = (timestamp) => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      boxes.forEach((box) => {
        // Subtle pulse animation
        const pulse = Math.sin(timestamp * box.pulseSpeed + box.pulsePhase) * 0.02
        let opacity = box.baseOpacity + pulse

        // Glow effect on hover
        if (box.glowIntensity > 0) {
          opacity += box.glowIntensity * 0.3
          box.glowIntensity *= 0.95 // Fade out glow
        }

        // Draw box
        ctx.strokeStyle = `rgba(139, 92, 246, ${opacity})`
        ctx.lineWidth = 1
        ctx.strokeRect(box.x, box.y, box.size - 1, box.size - 1)

        // Draw glow if active
        if (box.glowIntensity > 0.1) {
          const gradient = ctx.createRadialGradient(
            box.x + box.size / 2,
            box.y + box.size / 2,
            0,
            box.x + box.size / 2,
            box.y + box.size / 2,
            box.size
          )
          gradient.addColorStop(0, `rgba(139, 92, 246, ${box.glowIntensity * 0.4})`)
          gradient.addColorStop(0.5, `rgba(59, 130, 246, ${box.glowIntensity * 0.2})`)
          gradient.addColorStop(1, 'rgba(139, 92, 246, 0)')
          
          ctx.fillStyle = gradient
          ctx.fillRect(box.x - 10, box.y - 10, box.size + 20, box.size + 20)
        }
      })

      animationFrameId = requestAnimationFrame(drawBoxes)
    }

    // Mouse move handler
    const handleMouseMove = (e) => {
      const rect = canvas.getBoundingClientRect()
      const mouseX = e.clientX - rect.left
      const mouseY = e.clientY - rect.top

      boxes.forEach((box) => {
        const distance = Math.sqrt(
          Math.pow(mouseX - (box.x + box.size / 2), 2) +
          Math.pow(mouseY - (box.y + box.size / 2), 2)
        )

        if (distance < 100) {
          box.glowIntensity = Math.max(box.glowIntensity, 1 - distance / 100)
        }
      })
    }

    // Initialize
    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)
    canvas.addEventListener('mousemove', handleMouseMove)
    
    // Start animation
    animationFrameId = requestAnimationFrame(drawBoxes)

    // Cleanup
    return () => {
      window.removeEventListener('resize', resizeCanvas)
      canvas.removeEventListener('mousemove', handleMouseMove)
      cancelAnimationFrame(animationFrameId)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="animated-background"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: 0,
        pointerEvents: 'auto',
      }}
    />
  )
}

export default AnimatedBackground
