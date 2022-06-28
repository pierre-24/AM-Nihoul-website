// add title to each image, based on the alt desc
document.querySelectorAll('article img').forEach($e => {
  $e.title = $e.alt;
});

// add an anchor to each title, using the existing id or a new one if it does not exist
document.querySelectorAll('section h3').forEach($e => {
  let $link = document.createElement('a');
  let _id;

  if(!$e.id) {
    // (aggressively) slugify the text
    let txt = $e.innerHTML
      .replace(/<(.|\n)*?>/g, '')
      .replace(/[\s_.,?!]/g, ' ').trim()
      .replace(/\s+/g, '-')
      .replace(/[^0-9a-z\-]/gi, ''); // only [0-9a-z\-] is kept
    _id = txt.toLowerCase();
    // set the result as id
    $e.id = _id;
  } else {
    _id = $e.id; // use existing id
  }

  $link.innerText = '#';
  $link.href= '#' + _id;
  $link.classList.add('anchor');

  $e.appendChild($link);
});