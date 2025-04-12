function rgba2bgr(rgba_arr) {
    const result = new Uint8Array(rgba_arr.length / 4 * 3);
    for (let i = 0; i < rgba_arr.length; i += 4) {
        result[i / 4 * 3] = rgba_arr[i + 2];
        result[i / 4 * 3 + 1] = rgba_arr[i + 1];
        result[i / 4 * 3 + 2] = rgba_arr[i];
    }
    return result;
}

self.onmessage = async e => {
    let {
        frames,
        url
    } = e.data;

    frames = frames.map(rgba2bgr);

    await fetch(url, {
        method: "POST",
        body: new Blob([
            new Uint32Array([
                frames.length,
                frames[0].length
            ]),
            ...frames
        ])
    });

    self.postMessage("done");
}