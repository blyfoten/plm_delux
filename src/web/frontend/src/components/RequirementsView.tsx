const handleLinkClick = (url: string) => {
  // Remove any URL encoding of single quotes
  const decodedUrl = url.replace(/%27/g, "'");
  console.log("Opening URL (frontend):", decodedUrl);
  window.open(decodedUrl, '_blank');
}; 