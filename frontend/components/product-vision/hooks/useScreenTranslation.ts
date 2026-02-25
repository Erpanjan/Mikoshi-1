import { productVisionTranslations } from '../../../data/product-vision-translations';

export const useScreenTranslation = <K extends keyof typeof productVisionTranslations['en']>(screenKey: K) => {
  return productVisionTranslations.en[screenKey];
};
