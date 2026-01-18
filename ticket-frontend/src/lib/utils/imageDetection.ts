/**
 * Utility functions for detecting and extracting image URLs from text
 */

// Common image extensions
const IMAGE_EXTENSIONS = [
  'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'ico', 'tiff', 'tif'
];

// Pattern to match image URLs
const IMAGE_URL_PATTERN = new RegExp(
  `https?://[^\\s<>"{}|\\\\^[\`]+\\.(${IMAGE_EXTENSIONS.join('|')})(?:[?#][^\\s]*)?`,
  'gi'
);

// Pattern to match URLs that might contain images (like your Google example)
const POTENTIAL_IMAGE_URL_PATTERN = /https?:\/\/[^\s<>"{}|\\^[\`]+/gi;

/**
 * Extract all image URLs from text
 * @param text - The text to search for image URLs
 * @returns Array of unique image URLs found in the text
 */
export function extractImageUrls(text: string): string[] {
  if (!text) return [];
  
  const urls = new Set<string>();
  
  // Match direct image URLs (with common image extensions)
  const directMatches = text.match(IMAGE_URL_PATTERN);
  if (directMatches) {
    directMatches.forEach(url => urls.add(url));
  }
  
  // Match potential image URLs (including services like imgur, Google images, etc.)
  const potentialMatches = text.match(POTENTIAL_IMAGE_URL_PATTERN);
  if (potentialMatches) {
    potentialMatches.forEach(url => {
      // Check if URL is from known image hosting services
      if (isLikelyImageUrl(url)) {
        urls.add(url);
      }
    });
  }
  
  return Array.from(urls);
}

/**
 * Check if a URL is likely to be an image based on domain or query parameters
 * @param url - The URL to check
 * @returns True if the URL is likely an image
 */
function isLikelyImageUrl(url: string): boolean {
  const lowerUrl = url.toLowerCase();
  
  // Known image hosting services
  const imageHosts = [
    'imgur.com',
    'i.imgur.com',
    'gstatic.com', // Google images
    'googleusercontent.com',
    'cloudinary.com',
    'amazonaws.com', // S3
    'cloudfront.net',
    'flickr.com',
    'staticflickr.com',
    'photobucket.com',
    'imageshack.com',
    'tinypic.com',
    'postimg.cc',
    'imgbb.com',
    'ibb.co',
    'giphy.com',
    'tenor.com'
  ];
  
  // Check if URL contains image hosting domains
  if (imageHosts.some(host => lowerUrl.includes(host))) {
    return true;
  }
  
  // Check for image extensions
  if (IMAGE_EXTENSIONS.some(ext => lowerUrl.includes(`.${ext}`))) {
    return true;
  }
  
  return false;
}

/**
 * Check if text contains any image URLs
 * @param text - The text to check
 * @returns True if the text contains at least one image URL
 */
export function hasImageUrls(text: string): boolean {
  return extractImageUrls(text).length > 0;
}

/**
 * Replace image URLs in text with placeholders
 * Useful for displaying text without inline URLs
 * @param text - The text to process
 * @param placeholder - The placeholder text (default: "[Image]")
 * @returns Text with image URLs replaced
 */
export function replaceImageUrls(text: string, placeholder: string = '[Image]'): string {
  const imageUrls = extractImageUrls(text);
  let result = text;
  
  imageUrls.forEach(url => {
    result = result.replace(url, placeholder);
  });
  
  return result;
}
