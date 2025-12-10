import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Points, PointMaterial } from '@react-three/drei'
import * as THREE from 'three'

function ParticleNetwork() {
  const ref = useRef<THREE.Points>(null)
  const linesRef = useRef<THREE.LineSegments>(null)

  const { positions, connections } = useMemo(() => {
    const nodeCount = 100
    const positions = new Float32Array(nodeCount * 3)
    const connectionsList: number[] = []

    // Generate node positions in a spherical distribution
    for (let i = 0; i < nodeCount; i++) {
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)
      const radius = 3 + Math.random() * 2

      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta)
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta)
      positions[i * 3 + 2] = radius * Math.cos(phi)
    }

    // Create connections between nearby nodes
    for (let i = 0; i < nodeCount; i++) {
      for (let j = i + 1; j < nodeCount; j++) {
        const dx = positions[i * 3] - positions[j * 3]
        const dy = positions[i * 3 + 1] - positions[j * 3 + 1]
        const dz = positions[i * 3 + 2] - positions[j * 3 + 2]
        const distance = Math.sqrt(dx * dx + dy * dy + dz * dz)

        if (distance < 2 && Math.random() > 0.7) {
          connectionsList.push(
            positions[i * 3], positions[i * 3 + 1], positions[i * 3 + 2],
            positions[j * 3], positions[j * 3 + 1], positions[j * 3 + 2]
          )
        }
      }
    }

    return {
      positions,
      connections: new Float32Array(connectionsList),
    }
  }, [])

  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.x = state.clock.elapsedTime * 0.05
      ref.current.rotation.y = state.clock.elapsedTime * 0.08
    }
    if (linesRef.current) {
      linesRef.current.rotation.x = state.clock.elapsedTime * 0.05
      linesRef.current.rotation.y = state.clock.elapsedTime * 0.08
    }
  })

  return (
    <group>
      {/* Nodes */}
      <Points ref={ref} positions={positions} stride={3} frustumCulled={false}>
        <PointMaterial
          transparent
          color="#0ea5e9"
          size={0.08}
          sizeAttenuation={true}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </Points>

      {/* Connections */}
      <lineSegments ref={linesRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={connections.length / 3}
            array={connections}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial
          color="#0ea5e9"
          transparent
          opacity={0.15}
          blending={THREE.AdditiveBlending}
        />
      </lineSegments>
    </group>
  )
}

function FloatingOrbs() {
  const orb1Ref = useRef<THREE.Mesh>(null)
  const orb2Ref = useRef<THREE.Mesh>(null)

  useFrame((state) => {
    if (orb1Ref.current) {
      orb1Ref.current.position.x = Math.sin(state.clock.elapsedTime * 0.3) * 3
      orb1Ref.current.position.y = Math.cos(state.clock.elapsedTime * 0.4) * 2
      orb1Ref.current.position.z = Math.sin(state.clock.elapsedTime * 0.2) * 2
    }
    if (orb2Ref.current) {
      orb2Ref.current.position.x = Math.cos(state.clock.elapsedTime * 0.3) * 3
      orb2Ref.current.position.y = Math.sin(state.clock.elapsedTime * 0.5) * 2
      orb2Ref.current.position.z = Math.cos(state.clock.elapsedTime * 0.25) * 2
    }
  })

  return (
    <>
      <mesh ref={orb1Ref}>
        <sphereGeometry args={[0.15, 32, 32]} />
        <meshBasicMaterial color="#0ea5e9" transparent opacity={0.8} />
      </mesh>
      <mesh ref={orb2Ref}>
        <sphereGeometry args={[0.12, 32, 32]} />
        <meshBasicMaterial color="#a855f7" transparent opacity={0.8} />
      </mesh>
    </>
  )
}

export default function NetworkAnimation() {
  return (
    <Canvas camera={{ position: [0, 0, 8], fov: 60 }}>
      <color attach="background" args={['#020617']} />
      <ambientLight intensity={0.5} />
      <ParticleNetwork />
      <FloatingOrbs />
    </Canvas>
  )
}
