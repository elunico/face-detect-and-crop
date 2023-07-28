


function submitOne() {
  if (image.files.length < 1) {
    alert("Must choose an image file");
    return;
  }
  if (newheight.value === 0 && newwidth.value === 0) {
    alert("Cannot have 0x0 image. Specify at least one dimension");
    return;
  }
  let data = image.files[0];
  let reader = new FileReader();
  reader.readAsBinaryString(data);
  reader.addEventListener('load', ev => {
    let bdata = btoa(reader.result);
    let s = JSON.stringify({
      imagedata: bdata,
      newheight: newheight.value,
      newwidth: newwidth.value,
      mimetype: data.type,
      filename: data.name
    });

    doFetch('/do-shrink', s);
  });

}

function submitZip() {
  if (image.files.length < 1) {
    alert("Must choose a zip file");
    return;
  }
  if (newheight.value === 0 && newwidth.value === 0) {
    alert("Cannot have 0x0 image. Specify at least one dimension");
    return;
  }
  let data = image.files[0];
  let reader = new FileReader();
  reader.readAsBinaryString(data);
  reader.addEventListener('load', ev => {
    let bdata = btoa(reader.result);
    let s = JSON.stringify({
      imagedata: bdata,
      newheight: newheight.value,
      newwidth: newwidth.value,
      mimetype: data.type,
      filename: data.name,
    });

    doFetch('/do-shrinkall', s);
  });
}

function submit(type) {
  statusResponse.textContent = '';
  if (type == 'zip') {
    console.log('submitting zip');
    submitZip();
  } else {
    console.log('submitting one');
    submitOne();
  }

}
