export interface RecordingResult {
  audioBlob: Blob
  videoBlob: Blob | null
}

function chooseMimeType(): string | null {
  const candidates = [
    "video/webm;codecs=vp8,opus",
    "video/webm;codecs=vp9,opus",
    "video/webm",
    "video/mp4",
  ]
  for (const type of candidates) {
    if (typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(type)) {
      return type
    }
  }
  return null
}

function chooseAudioMimeType(): string {
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg"]
  for (const type of candidates) {
    if (typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(type)) {
      return type
    }
  }
  return "audio/webm"
}

export class DualRecorder {
  private audioRecorder: MediaRecorder
  private videoRecorder: MediaRecorder | null = null
  private audioChunks: BlobPart[] = []
  private videoChunks: BlobPart[] = []
  private audioMime: string
  private videoMime: string | null

  constructor(stream: MediaStream) {
    this.audioMime = chooseAudioMimeType()
    this.videoMime = chooseMimeType()

    const audioStream = new MediaStream(stream.getAudioTracks())
    this.audioRecorder = new MediaRecorder(audioStream, { mimeType: this.audioMime })
    this.audioRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) this.audioChunks.push(e.data)
    }

    if (this.videoMime && stream.getVideoTracks().length > 0) {
      this.videoRecorder = new MediaRecorder(stream, { mimeType: this.videoMime })
      this.videoRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) this.videoChunks.push(e.data)
      }
    }
  }

  get hasVideo() {
    return this.videoRecorder !== null
  }

  start() {
    this.audioChunks = []
    this.videoChunks = []
    this.audioRecorder.start(250)
    this.videoRecorder?.start(250)
  }

  stop(): Promise<RecordingResult> {
    return new Promise((resolve) => {
      let pending = this.videoRecorder ? 2 : 1

      const done = () => {
        pending -= 1
        if (pending === 0) {
          resolve({
            audioBlob: new Blob(this.audioChunks, { type: this.audioMime }),
            videoBlob: this.videoChunks.length
              ? new Blob(this.videoChunks, { type: this.videoMime! })
              : null,
          })
        }
      }

      this.audioRecorder.onstop = done
      if (this.videoRecorder) this.videoRecorder.onstop = done

      this.audioRecorder.stop()
      this.videoRecorder?.stop()
    })
  }
}
